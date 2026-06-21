import os
import threading
import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import uvicorn

from datetime import datetime
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    DEFAULT_LOGIN,
    DEFAULT_PASSWORD,
    DEFAULT_SERVER,
    FIB_GEN_SYMBOLS,
    FIB_JPY_SYMBOLS,
    FIB_KEYS as CONFIG_FIB_KEYS,
)

# ==============================================================
# GLOBAL CONFIG
# ==============================================================

ALL_SYMBOLS = list(set(FIB_GEN_SYMBOLS + FIB_JPY_SYMBOLS))

FIB_KEYS = CONFIG_FIB_KEYS

RSI_PERIOD = 14
HISTORY_CANDLES = 56

RSI_OVERBOUGHT = 80
RSI_OVERSOLD = 20

UPDATE_INTERVAL = 120

MA_CANDLES = 210
MA_THRESHOLD = 0.00015

# ==============================================================
# PYDANTIC MODELS
# ==============================================================

class HealthResponse(BaseModel):
    status: str
    mt5_connected: bool


# ==============================================================
# MT5 CONNECTION
# ==============================================================

_mt5_initialized = False
_mt5_lock = threading.Lock()


def initialize_mt5():
    global _mt5_initialized

    with _mt5_lock:
        if _mt5_initialized:
            return

        if not mt5.initialize():
            raise RuntimeError("MT5 initialize() failed")

        if not mt5.login(
            int(DEFAULT_LOGIN),
            DEFAULT_PASSWORD,
            DEFAULT_SERVER
        ):
            mt5.shutdown()
            raise RuntimeError("MT5 login failed")

        for sym in ALL_SYMBOLS:
            if not mt5.symbol_select(sym, True):
                print(f"WARNING: could not select {sym}")

        _mt5_initialized = True
        print("✅ MT5 initialized successfully")


def ensure_mt5():
    global _mt5_initialized

    if not mt5.terminal_info():
        _mt5_initialized = False
        initialize_mt5()


# ==============================================================
# FIB ENGINE
# ==============================================================

fib_lock = threading.Lock()
fib_stop = threading.Event()
fib_output = {"timestamp": None, "table": []}


def _calc_fib(symbol, timeframe):
    latest = mt5.copy_rates_from_pos(symbol, timeframe, 0, 2)

    if latest is None or len(latest) < 2:
        raise RuntimeError("No candles")

    end_dt = pd.to_datetime(
        latest[-1]["time"],
        unit="s",
        utc=True
    )

    start_dt = end_dt - pd.Timedelta(days=7)

    rates = mt5.copy_rates_range(
        symbol,
        timeframe,
        start_dt,
        end_dt
    )

    if rates is None or len(rates) < 5:
        raise RuntimeError("Not enough data")

    df = pd.DataFrame(rates)

    df["time"] = pd.to_datetime(
        df["time"],
        unit="s",
        utc=True
    ).dt.tz_convert(None)

    df.reset_index(drop=True, inplace=True)

    df["ind"] = (
        (df["close"] - df["open"]) / df["open"]
    ) * 100

    df["cum"] = df["ind"].cumsum()
    df["mid"] = df["cum"] / 2
    df["X"] = df["cum"].diff()

    df["isRedLocal"] = False

    for i in range(1, len(df)):
        X = df.loc[i, "X"]
        pm = df.loc[i - 1, "mid"]

        if pd.notna(X) and pd.notna(pm):
            if (
                ((X > 0 and pm < 0) or (X < 0 and pm > 0))
                and abs(X) > abs(pm)
            ):
                df.loc[i, "isRedLocal"] = True

    ref_tables = {}

    for ri in range(len(df) - 1):
        rows = []
        cv = None
        pm = None
        pc = None

        for i in range(ri, len(df)):
            ind = df.loc[i, "ind"]
            cv = ind if cv is None else cv + ind
            mid = cv / 2
            red = False

            if pm is not None:
                X = cv - pc
                if (
                    ((X > 0 and pm < 0) or (X < 0 and pm > 0))
                    and abs(X) > abs(pm)
                ):
                    red = True

            rows.append({
                "calc_time": df.loc[i, "time"],
                "Cum": cv,
                "Mid": mid,
                "RedLocal": red
            })

            pc = cv
            pm = mid

        ref_tables[df.loc[ri, "time"]] = pd.DataFrame(rows)

    fsig = pd.DataFrame([
        {
            "ref_datetime": rt,
            "finalGreen": not rdf.iloc[1:]["RedLocal"].any()
        }
        for rt, rdf in ref_tables.items()
    ])

    if fsig.empty or not fsig["finalGreen"].any():
        return {k: 0 for k in FIB_KEYS}, None

    trend_start = fsig.loc[
        fsig["finalGreen"],
        "ref_datetime"
    ].iloc[0]

    si = df.index[df["time"] == trend_start][0]

    dfa = df.loc[si:].copy()
    dfa["cum_from_start"] = dfa["ind"].cumsum()

    mi = dfa["cum_from_start"].abs().idxmax()

    direction = (
        "Uptrend"
        if df.loc[mi, "close"] > df.loc[si, "close"]
        else "Downtrend"
    )

    # Added Fib0 and Fib6 for identifying (n-1) and (n+1) price levels
    ratios = {
        "Fib0": 0.0,
        "Fib1": 0.236,
        "Fib2": 0.382,
        "Fib3": 0.5,
        "Fib4": 0.618,
        "Fib5": 0.786,
        "Fib6": 1.0,
    }

    sr = df.loc[si]
    mr = df.loc[mi]

    if direction == "Uptrend":
        h = mr["high"]
        l = sr["low"]
        rng = h - l
        levels = {
            k: h - v * rng
            for k, v in ratios.items()
        }
    else:
        h = sr["high"]
        l = mr["low"]
        rng = h - l
        levels = {
            k: l + v * rng
            for k, v in ratios.items()
        }

    sig = {k: 0 for k in FIB_KEYS}

    n2 = df.iloc[-3]
    n1 = df.iloc[-2]

    # Find closest level among Fib1 to Fib5 only
    signal_levels = {k: levels[k] for k in FIB_KEYS}
    fn, fp = min(
        signal_levels.items(),
        key=lambda x: abs(n2["close"] - x[1])
    )

    if direction == "Uptrend":
        if (
            n2["close"] < n2["open"]
            and abs(n2["close"] - fp) <= 0.0004 * fp
            and n1["close"] > n1["open"]
            and n1["close"] > n2["close"]
        ):
            sig[fn] = 1
    else:
        if (
            n2["close"] > n2["open"]
            and abs(n2["close"] - fp) <= 0.0004 * fp
            and n1["close"] < n1["open"]
            and n1["close"] < n2["close"]
        ):
            sig[fn] = 1

    info = {
        "TrendStart": str(df.loc[si, "time"]),
        "TrendEnd": str(df.loc[mi, "time"]),
        "TrendDirection": direction,
        "trade_direction": (
            "Potential Downside"
            if direction == "Uptrend"
            else "Potential Upside"
        ),
    }

    # If a signal is active for a Fib level n, identify n-1 and n+1 price levels
    if sig[fn] == 1:
        n = int(fn.replace("Fib", ""))
        prev_level_name = f"Fib{n-1}"
        next_level_name = f"Fib{n+1}"

        info["Fib_n_minus_1_Level"] = prev_level_name
        info["Fib_n_minus_1_Price"] = round(levels[prev_level_name], 5)
        info["Fib_n_plus_1_Level"] = next_level_name
        info["Fib_n_plus_1_Price"] = round(levels[next_level_name], 5)
        info["SignalLevelPrice"] = round(levels[fn], 5)

        # Standard keys for easy indexing/frontend rendering
        info[f"{prev_level_name}_Price"] = round(levels[prev_level_name], 5)
        info[f"{next_level_name}_Price"] = round(levels[next_level_name], 5)

    return sig, info


def _fib_engine(symbols, output, lock, stop, label):
    print(f"[{label}] started")
    tf_name = "15m"
    tf = mt5.TIMEFRAME_M15

    while not stop.is_set():
        ensure_mt5()
        rows = []

        for sym in symbols:
            try:
                fib, info = _calc_fib(sym, tf)
                row = {
                    "Symbol": sym.replace("m", ""),
                    "Timeframe": tf_name,
                    **fib,
                }
                if any(v == 1 for v in fib.values()) and info:
                    row.update(info)
            except Exception as e:
                print(f"[{label}] Error on {sym}: {e}")
                row = {
                    "Symbol": sym.replace("m", ""),
                    "Timeframe": tf_name,
                    **{k: 0 for k in FIB_KEYS},
                }
            rows.append(row)

        with lock:
            output["timestamp"] = datetime.utcnow().isoformat()
            output["table"] = rows

        print(f"[{label}] updated")
        stop.wait(UPDATE_INTERVAL)


# ==============================================================
# RSI ENGINE
# ==============================================================

rsi_lock = threading.Lock()
rsi_stop = threading.Event()
rsi_results = []
rsi_ob_os = []


def _calc_rsi_array(net_changes):
    gains = net_changes[net_changes > 0]
    losses = net_changes[net_changes < 0]

    avg_gain = gains.sum() / RSI_PERIOD
    avg_loss = abs(losses.sum()) / RSI_PERIOD

    if avg_loss == 0:
        return 100.0

    return 100 - (100 / (1 + avg_gain / avg_loss))


def _process_rsi_symbol(symbol, timeframe, tf_name):
    total = RSI_PERIOD + HISTORY_CANDLES + 1
    rates = mt5.copy_rates_from_pos(
        symbol,
        timeframe,
        0,
        total
    )

    if rates is None or len(rates) < total:
        return None

    df = pd.DataFrame(rates).iloc[:-1]
    df["net_pct"] = (
        (df["close"] - df["open"]) / df["open"]
    ) * 100

    lw = df.tail(RSI_PERIOD)
    nc = lw["net_pct"].values

    rsi = _calc_rsi_array(nc)
    sd = np.std(nc)

    pc = (
        nc[-1] - 2 * sd
        if rsi > 50
        else nc[-1] + 2 * sd
    )

    adj = _calc_rsi_array(np.append(nc[1:], pc))

    label = (
        "Overbought"
        if rsi > RSI_OVERBOUGHT
        else (
            "Oversold"
            if rsi < RSI_OVERSOLD
            else "NA"
        )
    )

    return {
        "symbol": symbol,
        "timeframe": tf_name,
        "RSI": round(rsi, 2),
        "Adjusted_RSI": round(adj, 2),
        "ob_os": label,
    }


def _rsi_engine(symbols, lock, results, ob_os, stop, label):
    print(f"[{label}] started")
    tf_name = "1h"
    tf = mt5.TIMEFRAME_H1

    while not stop.is_set():
        ensure_mt5()
        tr = []
        to = []

        for sym in symbols:
            try:
                rd = _process_rsi_symbol(sym, tf, tf_name)
                if rd:
                    tr.append(rd)
                    to.append({
                        "symbol": rd["symbol"],
                        "timeframe": rd["timeframe"],
                        "RSI": rd["RSI"],
                        "ob_os": rd["ob_os"],
                    })
            except Exception as e:
                print(f"[{label}] Error on {sym}: {e}")

        with lock:
            results.clear()
            results.extend(tr)
            ob_os.clear()
            ob_os.extend(to)

        print(f"[{label}] updated")
        time.sleep(UPDATE_INTERVAL)


# ==============================================================
# MA ENGINE
# ==============================================================

ma_lock = threading.Lock()
ma_stop = threading.Event()
ma_results = []


def _ma_signal(s21, prev_s21, sma_x):
    if pd.isna(s21) or pd.isna(prev_s21) or pd.isna(sma_x) or sma_x == 0:
        return "NA"

    diff = s21 - sma_x
    abs_rel_diff = abs(diff / sma_x)

    if abs_rel_diff < MA_THRESHOLD:
        if diff > 0 and s21 > prev_s21:
            return 1
        if diff < 0 and s21 < prev_s21:
            return -1

    return "NA"


def _get_ma_signals(symbols):
    results = []
    tf_name = "15m"
    tf = mt5.TIMEFRAME_M15

    for sym in symbols:
        if not mt5.symbol_select(sym, True):
            continue

        rates = mt5.copy_rates_from_pos(
            sym,
            tf,
            0,
            MA_CANDLES + 1
        )

        if rates is None or len(rates) < MA_CANDLES:
            results.append({
                "Symbol": sym,
                "Timeframe": tf_name,
                "SMA50_Signal": "NA",
                "SMA100_Signal": "NA",
                "SMA200_Signal": "NA",
                "Error": "Insufficient Data",
            })
            continue

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(
            df["time"],
            unit="s"
        )

        df["SMA21"] = (
            df["close"].rolling(21).mean()
        )
        df["SMA50"] = (
            df["close"].rolling(50).mean()
        )
        df["SMA100"] = (
            df["close"].rolling(100).mean()
        )
        df["SMA200"] = (
            df["close"].rolling(200).mean()
        )

        closed = df.iloc[-2]
        prev_s21 = df.iloc[-3]["SMA21"]
        s21 = closed["SMA21"]

        results.append({
            "Symbol": sym,
            "Timeframe": tf_name,
            "SMA50_Signal": _ma_signal(
                s21,
                prev_s21,
                closed["SMA50"]
            ),
            "SMA100_Signal": _ma_signal(
                s21,
                prev_s21,
                closed["SMA100"]
            ),
            "SMA200_Signal": _ma_signal(
                s21,
                prev_s21,
                closed["SMA200"]
            ),
            "Last Close": round(
                float(closed["close"]),
                5
            ),
            "Time": closed["time"].strftime(
                "%Y-%m-%d %H:%M"
            ),
        })

    return results


def _ma_engine(symbols, results, lock, stop, label):
    print(f"[{label}] started")

    while not stop.is_set():
        ensure_mt5()
        try:
            data = _get_ma_signals(symbols)
            with lock:
                results.clear()
                results.extend(data)
        except Exception as e:
            print(f"[{label}] Error updating MA signals: {e}")

        print(f"[{label}] updated")
        time.sleep(UPDATE_INTERVAL)


# ==============================================================
# FASTAPI LIFESPAN
# ==============================================================

_all_threads = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_mt5()

    threads_cfg = [
        (
            fib_stop,
            _fib_engine,
            (
                ALL_SYMBOLS,
                fib_output,
                fib_lock,
                fib_stop,
                "FIB-ALL",
            ),
        ),
        (
            rsi_stop,
            _rsi_engine,
            (
                ALL_SYMBOLS,
                rsi_lock,
                rsi_results,
                rsi_ob_os,
                rsi_stop,
                "RSI-ALL",
            ),
        ),
        (
            ma_stop,
            _ma_engine,
            (
                ALL_SYMBOLS,
                ma_results,
                ma_lock,
                ma_stop,
                "MA-ALL",
            ),
        ),
    ]

    for stop_ev, fn, args in threads_cfg:
        stop_ev.clear()
        t = threading.Thread(
            target=fn,
            args=args,
            daemon=True
        )
        t.start()
        _all_threads.append((stop_ev, t))

    yield

    for stop_ev, t in _all_threads:
        stop_ev.set()

    for _, t in _all_threads:
        t.join(timeout=5)

    mt5.shutdown()
    print("🔴 MT5 shutdown")


# ==============================================================
# FASTAPI APP
# ==============================================================

app = FastAPI(
    title="Orivis Alpha – Combined Engine API",
    version="1.0.0",
    description="""
    Institutional-grade Forex Analytics API powered by MetaTrader5.

    Features:
    - Fibonacci trend engine (15m)
    - RSI analytics engine (1h)
    - Overbought/Oversold detection
    - Moving average signal engine (15m)
    """,
    servers=[
        {
            "url": "http://74.208.190.247:8000",
            "description": "Production VPS Server"
        }
    ],
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================
# HEALTH
# ==============================================================

@app.get(
    "/health",
    tags=["System"],
    summary="Check API and MT5 connection health",
    response_model=HealthResponse,
)
def health():
    return {
        "status": "running",
        "mt5_connected": bool(mt5.terminal_info()),
    }


# ==============================================================
# FIBONACCI
# ==============================================================

@app.get(
    "/fib/signal",
    tags=["Fibonacci"],
    summary="Get Fibonacci signals for all forex pairs",
)
def fib_signal():
    with fib_lock:
        return {
            "status": (
                "ok"
                if fib_output["table"]
                else "warming_up"
            ),
            "timestamp": fib_output["timestamp"],
            "table": fib_output["table"],
        }


# ==============================================================
# RSI
# ==============================================================

@app.get(
    "/rsi/rsi",
    tags=["RSI"],
    summary="Get RSI analytics for all forex pairs",
)
def rsi_get():
    with rsi_lock:
        return {
            "timestamp": datetime.now(),
            "data": rsi_results,
        }


@app.get(
    "/rsi/rsi-ob-os",
    tags=["RSI"],
    summary="Get RSI overbought and oversold signals for all pairs",
)
def rsi_obos():
    with rsi_lock:
        return {
            "timestamp": datetime.now(),
            "overbought_threshold": RSI_OVERBOUGHT,
            "oversold_threshold": RSI_OVERSOLD,
            "data": rsi_ob_os,
        }


# ==============================================================
# MOVING AVERAGE
# ==============================================================

@app.get(
    "/ma/signals",
    tags=["Moving Average"],
    summary="Get moving average crossover signals for all forex pairs",
)
def ma_get():
    with ma_lock:
        return {
            "status": "success",
            "data": ma_results,
        }


# ==============================================================
# PROBABILITY SCORE
# ==============================================================

@app.get(
    "/probability/score",
    tags=["Probability Score"],
    summary="Get combined probability score for symbols with active Fib 2, 3, or 4 levels",
)
def probability_score():
    with fib_lock:
        fib_table = list(fib_output.get("table", []))
    with rsi_lock:
        rsi_list = list(rsi_results)
    with ma_lock:
        ma_list = list(ma_results)

    def normalize_symbol(sym: str) -> str:
        if not sym:
            return ""
        return sym.replace("m", "").upper()

    rsi_map = {normalize_symbol(item.get("symbol", "")): item for item in rsi_list if "symbol" in item}
    ma_map = {normalize_symbol(item.get("Symbol", "")): item for item in ma_list if "Symbol" in item}

    results = []

    for row in fib_table:
        sym = row.get("Symbol", "")
        norm_sym = normalize_symbol(sym)
        
        fib2_active = row.get("Fib2") == 1
        fib3_active = row.get("Fib3") == 1
        fib4_active = row.get("Fib4") == 1
        trend_dir = row.get("TrendDirection")

        # Select symbols where Fib 2, 3, or 4 is active and trend direction is present
        if trend_dir in ("Uptrend", "Downtrend") and (fib2_active or fib3_active or fib4_active):
            # Calculate Fib score
            fib_score = 0
            active_fib = None
            if fib2_active:
                fib_score = 70
                active_fib = "Fib2"
            elif fib3_active:
                fib_score = 80
                active_fib = "Fib3"
            elif fib4_active:
                fib_score = 70
                active_fib = "Fib4"

            # Calculate RSI score
            rsi_score = 0
            rsi_val = None
            rsi_item = rsi_map.get(norm_sym)
            if rsi_item is not None:
                rsi_val = rsi_item.get("RSI")
                if rsi_val is not None:
                    if trend_dir == "Downtrend":
                        if rsi_val < 20:
                            rsi_score = 100
                        elif 60 <= rsi_val <= 70:
                            rsi_score = 70
                        elif 70 < rsi_val <= 75:
                            rsi_score = 80
                        elif 75 < rsi_val <= 80:
                            rsi_score = 90
                    elif trend_dir == "Uptrend":
                        if rsi_val > 80:
                            rsi_score = 100
                        elif 30 <= rsi_val <= 40:
                            rsi_score = 70
                        elif 25 <= rsi_val < 30:
                            rsi_score = 80
                        elif 20 <= rsi_val < 25:
                            rsi_score = 90

            # Calculate SMA score
            sma_score = 0
            sig50 = "NA"
            sig100 = "NA"
            sig200 = "NA"
            ma_item = ma_map.get(norm_sym)
            if ma_item is not None:
                sig50 = ma_item.get("SMA50_Signal", "NA")
                sig100 = ma_item.get("SMA100_Signal", "NA")
                sig200 = ma_item.get("SMA200_Signal", "NA")

                active_smas = []
                if sig50 in (1, -1, "1", "-1"):
                    active_smas.append("SMA50")
                if sig100 in (1, -1, "1", "-1"):
                    active_smas.append("SMA100")
                if sig200 in (1, -1, "1", "-1"):
                    active_smas.append("SMA200")

                if len(active_smas) > 1:
                    # Active simultaneously for multiple levels
                    sma_score = 70
                elif len(active_smas) == 1:
                    level = active_smas[0]
                    if level == "SMA50":
                        sma_score = 70
                    elif level == "SMA100":
                        sma_score = 90
                    elif level == "SMA200":
                        sma_score = 70

            # Calculate total score
            total_score = round(0.33 * fib_score + 0.33 * rsi_score + 0.33 * sma_score, 2)

            trade_dir = "Potential Downside" if trend_dir == "Uptrend" else "Potential Upside"
            item = {
                "Symbol": sym,
                "trade_direction": trade_dir,
                "ActiveFibLevel": active_fib,
                "FibScore": fib_score,
                "RSI_Value": rsi_val,
                "RSIScore": rsi_score,
                "SMA50_Signal": sig50,
                "SMA100_Signal": sig100,
                "SMA200_Signal": sig200,
                "SMAScore": sma_score,
                "TotalScore": total_score
            }

            # If score is > 50 and specific RSI/trend conditions are met, calculate and display trade parameters
            should_display_trade = False
            if total_score > 50 and rsi_val is not None:
                if trend_dir == "Downtrend" and (60 < rsi_val <= 80 or rsi_val < 20):
                    should_display_trade = True
                elif trend_dir == "Uptrend" and (20 < rsi_val < 40 or rsi_val > 80):
                    should_display_trade = True

            if should_display_trade:
                fib_n_price = row.get("SignalLevelPrice")
                fib_n_plus_1_price = row.get("Fib_n_plus_1_Price")

                if fib_n_price is not None and fib_n_plus_1_price is not None:
                    item["EntryPrice"] = round(fib_n_price, 5)
                    if trend_dir == "Downtrend":
                        tp = fib_n_plus_1_price + 0.0003 * fib_n_price
                        sl = fib_n_price - (tp - fib_n_price) * 0.8
                    else:  # Uptrend
                        tp = fib_n_plus_1_price - 0.0003 * fib_n_price
                        sl = fib_n_price + (fib_n_price - tp) * 0.8

                    item["TargetProfit"] = round(tp, 5)
                    item["StopLoss"] = round(sl, 5)

                # Only include items that meet the final display criteria
                results.append(item)

    return {
        "status": "success",
        "timestamp": datetime.now(),
        "count": len(results),
        "data": results
    }


# ==============================================================
# ENTRYPOINT
# ==============================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )

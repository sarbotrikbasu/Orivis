import os
import threading
import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import (
    DEFAULT_LOGIN, DEFAULT_PASSWORD, DEFAULT_SERVER,
    FIB_GEN_SYMBOLS, FIB_JPY_SYMBOLS,
    TIMEFRAMES as ENV_TIMEFRAMES,
    FIB_KEYS as CONFIG_FIB_KEYS,
)

# ==============================================================
# GLOBAL CONFIG
# ==============================================================

FIB_GEN_SYMS = FIB_GEN_SYMBOLS
FIB_JPY_SYMS = FIB_JPY_SYMBOLS
ALL_SYMBOLS  = list(set(FIB_GEN_SYMS + FIB_JPY_SYMS))

TIMEFRAME_MAP = {
    "5m":  mt5.TIMEFRAME_M5,
    "15m": mt5.TIMEFRAME_M15,
    "1h":  mt5.TIMEFRAME_H1,
    "1d":  mt5.TIMEFRAME_D1,
}
TF_DICT = {k: TIMEFRAME_MAP[k] for k in ENV_TIMEFRAMES if k in TIMEFRAME_MAP}

FIB_KEYS        = CONFIG_FIB_KEYS
RSI_PERIOD      = 14
HISTORY_CANDLES = 56
RSI_OVERBOUGHT  = 80
RSI_OVERSOLD    = 20
SMA_PERIOD      = 20
LOOKBACK_CANDLES = 200
UPDATE_INTERVAL = 120

# ==============================================================
# MT5 — SINGLE SHARED CONNECTION
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
        if not mt5.login(int(DEFAULT_LOGIN), DEFAULT_PASSWORD, DEFAULT_SERVER):
            mt5.shutdown()
            raise RuntimeError("MT5 login failed")
        for sym in ALL_SYMBOLS:
            if not mt5.symbol_select(sym, True):
                print(f"WARNING: could not select {sym}")
        _mt5_initialized = True
        print("✅ MT5 ready – all symbols selected")

def ensure_mt5():
    if not mt5.terminal_info():
        global _mt5_initialized
        _mt5_initialized = False
        initialize_mt5()

# ==============================================================
# SECTION 1 – FIB ENGINE  (Gen + JPY)
# ==============================================================

fib_gen_lock   = threading.Lock()
fib_gen_stop   = threading.Event()
fib_gen_output = {"timestamp": None, "table": []}

fib_jpy_lock   = threading.Lock()
fib_jpy_stop   = threading.Event()
fib_jpy_output = {"timestamp": None, "table": []}


def _calc_fib(symbol, timeframe):
    latest = mt5.copy_rates_from_pos(symbol, timeframe, 0, 2)
    if latest is None or len(latest) < 2:
        raise RuntimeError("no candles")
    end_dt   = pd.to_datetime(latest[-1]["time"], unit="s", utc=True)
    start_dt = end_dt - pd.Timedelta(days=7)
    rates = mt5.copy_rates_range(symbol, timeframe, start_dt, end_dt)
    if rates is None or len(rates) < 5:
        raise RuntimeError("not enough data")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert(None)
    df.reset_index(drop=True, inplace=True)
    df["ind"] = ((df["close"] - df["open"]) / df["open"]) * 100
    df["cum"] = df["ind"].cumsum()
    df["mid"] = df["cum"] / 2
    df["X"]   = df["cum"].diff()
    df["isRedLocal"] = False
    for i in range(1, len(df)):
        X, pm = df.loc[i, "X"], df.loc[i - 1, "mid"]
        if pd.notna(X) and pd.notna(pm):
            if ((X > 0 and pm < 0) or (X < 0 and pm > 0)) and abs(X) > abs(pm):
                df.loc[i, "isRedLocal"] = True
    ref_tables = {}
    for ri in range(len(df) - 1):
        rows, cv, pm, pc = [], None, None, None
        for i in range(ri, len(df)):
            ind = df.loc[i, "ind"]
            cv  = ind if cv is None else cv + ind
            mid = cv / 2
            red = False
            if pm is not None:
                X = cv - pc
                if ((X > 0 and pm < 0) or (X < 0 and pm > 0)) and abs(X) > abs(pm):
                    red = True
            rows.append({"calc_time": df.loc[i, "time"], "Cum": cv, "Mid": mid, "RedLocal": red})
            pc, pm = cv, mid
        ref_tables[df.loc[ri, "time"]] = pd.DataFrame(rows)
    fsig = pd.DataFrame([
        {"ref_datetime": rt, "finalGreen": not rdf.iloc[1:]["RedLocal"].any()}
        for rt, rdf in ref_tables.items()
    ])
    if fsig.empty or not fsig["finalGreen"].any():
        return {k: 0 for k in FIB_KEYS}, None
    trend_start = fsig.loc[fsig["finalGreen"], "ref_datetime"].iloc[0]
    si = df.index[df["time"] == trend_start][0]
    dfa = df.loc[si:].copy()
    dfa["cum_from_start"] = dfa["ind"].cumsum()
    mi = dfa["cum_from_start"].abs().idxmax()
    direction = "Uptrend" if df.loc[mi, "close"] > df.loc[si, "close"] else "Downtrend"
    ratios = {"Fib1": 0.236, "Fib2": 0.382, "Fib3": 0.5, "Fib4": 0.618, "Fib5": 0.786}
    sr, mr = df.loc[si], df.loc[mi]
    if direction == "Uptrend":
        h, l = mr["high"], sr["low"]; rng = h - l
        levels = {k: h - v * rng for k, v in ratios.items()}
    else:
        h, l = sr["high"], mr["low"]; rng = h - l
        levels = {k: l + v * rng for k, v in ratios.items()}
    sig = {k: 0 for k in FIB_KEYS}
    n2, n1 = df.iloc[-3], df.iloc[-2]
    fn, fp = min(levels.items(), key=lambda x: abs(n2["close"] - x[1]))
    if direction == "Uptrend":
        if n2["close"] < n2["open"] and abs(n2["close"] - fp) <= 0.0005 * fp and n1["close"] > n1["open"] and n1["close"] > n2["close"]:
            sig[fn] = 1
    else:
        if n2["close"] > n2["open"] and abs(n2["close"] - fp) <= 0.0005 * fp and n1["close"] < n1["open"] and n1["close"] < n2["close"]:
            sig[fn] = 1
    return sig, {"TrendStart": str(df.loc[si, "time"]), "TrendEnd": str(df.loc[mi, "time"]), "TrendDirection": direction}


def _fib_engine(symbols, output, lock, stop, label):
    print(f"[{label}] Fib engine started")
    while not stop.is_set():
        ensure_mt5()
        rows = []
        for sym in symbols:
            for tf_name, tf in TF_DICT.items():
                try:
                    fib, info = _calc_fib(sym, tf)
                    row = {"Symbol": sym.replace("m", ""), "Timeframe": tf_name, **fib}
                    if any(v == 1 for v in fib.values()) and info:
                        row.update(info)
                except Exception:
                    row = {"Symbol": sym.replace("m", ""), "Timeframe": tf_name, **{k: 0 for k in FIB_KEYS}}
                rows.append(row)
        with lock:
            output["timestamp"] = datetime.utcnow().isoformat()
            output["table"]     = rows
        print(f"[{label}] updated {datetime.now()}")
        stop.wait(UPDATE_INTERVAL)
    print(f"[{label}] Fib engine stopped")

# ==============================================================
# SECTION 2 – RSI ENGINE  (Gen + JPY)
# ==============================================================

rsi_gen_lock       = threading.Lock()
rsi_gen_stop       = threading.Event()
rsi_gen_results    = []
rsi_gen_ob_os      = []
rsi_gen_divergence = []

rsi_jpy_lock       = threading.Lock()
rsi_jpy_stop       = threading.Event()
rsi_jpy_results    = []
rsi_jpy_ob_os      = []
rsi_jpy_divergence = []


def _calc_rsi_array(net_changes):
    gains    = net_changes[net_changes > 0]
    losses   = net_changes[net_changes < 0]
    avg_gain = gains.sum() / RSI_PERIOD
    avg_loss = abs(losses.sum()) / RSI_PERIOD
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))


def _process_rsi_symbol(symbol, timeframe, tf_name):
    total = RSI_PERIOD + HISTORY_CANDLES + 1
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, total)
    if rates is None or len(rates) < total:
        return None, None
    df = pd.DataFrame(rates).iloc[:-1]
    df["net_pct"] = ((df["close"] - df["open"]) / df["open"]) * 100
    lw  = df.tail(RSI_PERIOD)
    nc  = lw["net_pct"].values
    rsi = _calc_rsi_array(nc)
    sd  = np.std(nc)
    pc  = nc[-1] - 2 * sd if rsi > 50 else nc[-1] + 2 * sd
    adj = _calc_rsi_array(np.append(nc[1:], pc))
    label = "Overbought" if rsi > RSI_OVERBOUGHT else ("Oversold" if rsi < RSI_OVERSOLD else "NA")
    rsi_result = {"symbol": symbol, "timeframe": tf_name, "RSI": round(rsi, 2), "Adjusted_RSI": round(adj, 2), "ob_os": label}
    df["RSI"] = np.nan
    for i in range(RSI_PERIOD, len(df)):
        df.loc[df.index[i], "RSI"] = _calc_rsi_array(df["net_pct"].iloc[i - RSI_PERIOD:i].values)
    li = df.index[-1]
    lcp, lrv = df.loc[li, "close"], df.loc[li, "RSI"]
    div_found, div_ts, div_type = False, None, None
    for _, row in df.tail(HISTORY_CANDLES + 1).iloc[:-1].iterrows():
        if lcp > row["close"] and lrv < row["RSI"]:
            div_found, div_ts, div_type = True, datetime.fromtimestamp(row["time"]), "Bearish"; break
        if lcp < row["close"] and lrv > row["RSI"]:
            div_found, div_ts, div_type = True, datetime.fromtimestamp(row["time"]), "Bullish"; break
    div_result = {"symbol": symbol, "timeframe": tf_name, "divergence": div_found, "divergence_type": div_type, "divergence_candle_timestamp": div_ts}
    return rsi_result, div_result


def _rsi_engine(symbols, lock, results, ob_os, divergence, stop, label):
    print(f"[{label}] RSI engine started")
    while not stop.is_set():
        ensure_mt5()
        tr, to, td = [], [], []
        for sym in symbols:
            for tf_name, tf in TF_DICT.items():
                rd, dd = _process_rsi_symbol(sym, tf, tf_name)
                if rd:
                    tr.append(rd)
                    to.append({"symbol": rd["symbol"], "timeframe": rd["timeframe"], "RSI": rd["RSI"], "ob_os": rd["ob_os"]})
                if dd:
                    td.append(dd)
        with lock:
            results.clear();    results.extend(tr)
            ob_os.clear();      ob_os.extend(to)
            divergence.clear(); divergence.extend(td)
        print(f"[{label}] updated {datetime.now()}")
        time.sleep(UPDATE_INTERVAL)
    print(f"[{label}] RSI engine stopped")

# ==============================================================
# SECTION 3 – BOLLINGER ENGINE  (Gen + JPY)
# ==============================================================

boll_gen_lock   = threading.Lock()
boll_gen_stop   = threading.Event()
boll_gen_output = {"timestamp": None, "data": {}}

boll_jpy_lock   = threading.Lock()
boll_jpy_stop   = threading.Event()
boll_jpy_output = {"timestamp": None, "data": {}}


def _calc_bollinger(symbol, timeframe):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, LOOKBACK_CANDLES + SMA_PERIOD + 5)
    if rates is None or len(rates) < LOOKBACK_CANDLES + SMA_PERIOD:
        return None
    df = pd.DataFrame(rates).iloc[:-1]
    df["SMA"] = df["close"].rolling(SMA_PERIOD).mean()
    df["STD"] = df["close"].rolling(SMA_PERIOD).std()
    df["Range"] = 4 * df["STD"]
    cur = df.iloc[-1]
    rs  = df["Range"].iloc[-LOOKBACK_CANDLES:]
    return {
        "SMA":         round(float(cur["SMA"]), 6),
        "UpperBand":   round(float(cur["SMA"] + 2 * cur["STD"]), 6),
        "LowerBand":   round(float(cur["SMA"] - 2 * cur["STD"]), 6),
        "CurrentRange": round(float(cur["Range"]), 6),
        "MaxRange":    round(float(rs.max()), 6),
        "MinRange":    round(float(rs.min()), 6),
        "LastClosedTime": str(datetime.fromtimestamp(cur["time"])),
    }


def _bollinger_engine(symbols, output, lock, stop, label):
    print(f"[{label}] Bollinger engine started")
    while not stop.is_set():
        ensure_mt5()
        tmp = {}
        for sym in symbols:
            tmp[sym] = {}
            for tf_name, tf in TF_DICT.items():
                r = _calc_bollinger(sym, tf)
                if r:
                    tmp[sym][tf_name] = r
        with lock:
            output["timestamp"] = str(datetime.utcnow())
            output["data"]      = tmp
        print(f"[{label}] updated {datetime.now()}")
        stop.wait(UPDATE_INTERVAL)
    print(f"[{label}] Bollinger engine stopped")

# ==============================================================
# SECTION 4 – MA ENGINE  (Gen + JPY)
# ==============================================================

ma_gen_lock   = threading.Lock()
ma_gen_stop   = threading.Event()
ma_gen_results = []

ma_jpy_lock   = threading.Lock()
ma_jpy_stop   = threading.Event()
ma_jpy_results = []


def _get_ma_signals(symbols):
    results = []
    for sym in symbols:
        for tf_name, tf in TF_DICT.items():
            if not mt5.symbol_select(sym, True):
                continue
            rates = mt5.copy_rates_from_pos(sym, tf, 0, 250)
            if rates is None or len(rates) == 0:
                results.append({"Symbol": sym, "Timeframe": tf_name, "SMA50": -1, "SMA100": -1, "SMA200": -1, "Error": "No Data"})
                continue
            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df["SMA21"]  = df["close"].rolling(21).mean()
            df["SMA50"]  = df["close"].rolling(50).mean()
            df["SMA100"] = df["close"].rolling(100).mean()
            df["SMA200"] = df["close"].rolling(200).mean()
            latest = df.iloc[-1]
            def chk(s21, st):
                if s21 == 0 or pd.isna(s21) or pd.isna(st): return 0
                return 1 if abs((s21 - st) / s21) <= 0.001 else 0
            s21 = latest["SMA21"]
            results.append({
                "Symbol":     sym,
                "Timeframe":  tf_name,
                "SMA50":      chk(s21, latest["SMA50"]),
                "SMA100":     chk(s21, latest["SMA100"]),
                "SMA200":     chk(s21, latest["SMA200"]),
                "Last Close": round(latest["close"], 5),
                "Time":       latest["time"].strftime("%Y-%m-%d %H:%M"),
            })
    return results


def _ma_engine(symbols, results, lock, stop, label):
    print(f"[{label}] MA engine started")
    while not stop.is_set():
        ensure_mt5()
        data = _get_ma_signals(symbols)
        with lock:
            results.clear()
            results.extend(data)
        print(f"[{label}] updated {datetime.now()}")
        time.sleep(UPDATE_INTERVAL)
    print(f"[{label}] MA engine stopped")

# ==============================================================
# LIFESPAN – start / stop all engines
# ==============================================================

_all_threads = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_mt5()

    threads_cfg = [
        (fib_gen_stop,  _fib_engine,       (FIB_GEN_SYMS, fib_gen_output, fib_gen_lock, fib_gen_stop, "FIB-GEN")),
        (fib_jpy_stop,  _fib_engine,       (FIB_JPY_SYMS, fib_jpy_output, fib_jpy_lock, fib_jpy_stop, "FIB-JPY")),
        (rsi_gen_stop,  _rsi_engine,       (FIB_GEN_SYMS, rsi_gen_lock, rsi_gen_results, rsi_gen_ob_os, rsi_gen_divergence, rsi_gen_stop, "RSI-GEN")),
        (rsi_jpy_stop,  _rsi_engine,       (FIB_JPY_SYMS, rsi_jpy_lock, rsi_jpy_results, rsi_jpy_ob_os, rsi_jpy_divergence, rsi_jpy_stop, "RSI-JPY")),
        (boll_gen_stop, _bollinger_engine, (FIB_GEN_SYMS, boll_gen_output, boll_gen_lock, boll_gen_stop, "BOLL-GEN")),
        (boll_jpy_stop, _bollinger_engine, (FIB_JPY_SYMS, boll_jpy_output, boll_jpy_lock, boll_jpy_stop, "BOLL-JPY")),
        (ma_gen_stop,   _ma_engine,        (FIB_GEN_SYMS, ma_gen_results, ma_gen_lock, ma_gen_stop, "MA-GEN")),
        (ma_jpy_stop,   _ma_engine,        (FIB_JPY_SYMS, ma_jpy_results, ma_jpy_lock, ma_jpy_stop, "MA-JPY")),
    ]

    for stop_ev, fn, args in threads_cfg:
        stop_ev.clear()
        t = threading.Thread(target=fn, args=args, daemon=True)
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

app = FastAPI(title="Orivis Alpha – Combined Engine", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Health ---

@app.get("/health")
def health():
    return {"status": "running", "mt5_connected": bool(mt5.terminal_info())}

# --- Fib Gen ---

@app.get("/fib-gen/signal")
def fib_gen_signal():
    with fib_gen_lock:
        return {"status": "ok" if fib_gen_output["table"] else "warming_up",
                "timestamp": fib_gen_output["timestamp"], "table": fib_gen_output["table"]}

# --- Fib JPY ---

@app.get("/fib-jpy/signal")
def fib_jpy_signal():
    with fib_jpy_lock:
        return {"status": "ok" if fib_jpy_output["table"] else "warming_up",
                "timestamp": fib_jpy_output["timestamp"], "table": fib_jpy_output["table"]}

# --- RSI Gen ---

@app.get("/rsi-gen/rsi")
def rsi_gen_get():
    with rsi_gen_lock:
        return {"timestamp": datetime.now(), "data": rsi_gen_results}

@app.get("/rsi-gen/rsi-ob-os")
def rsi_gen_obos():
    with rsi_gen_lock:
        return {"timestamp": datetime.now(), "overbought_threshold": RSI_OVERBOUGHT,
                "oversold_threshold": RSI_OVERSOLD, "data": rsi_gen_ob_os}

# --- RSI JPY ---

@app.get("/rsi-jpy/rsi")
def rsi_jpy_get():
    with rsi_jpy_lock:
        return {"timestamp": datetime.now(), "data": rsi_jpy_results}

@app.get("/rsi-jpy/rsi-ob-os")
def rsi_jpy_obos():
    with rsi_jpy_lock:
        return {"timestamp": datetime.now(), "overbought_threshold": RSI_OVERBOUGHT,
                "oversold_threshold": RSI_OVERSOLD, "data": rsi_jpy_ob_os}

# --- Bollinger Gen ---

@app.get("/bollinger-gen/bollinger")
def boll_gen_get():
    with boll_gen_lock:
        if not boll_gen_output["data"]:
            raise HTTPException(status_code=503, detail="Data not ready")
        return boll_gen_output

# --- Bollinger JPY ---

@app.get("/bollinger-jpy/bollinger")
def boll_jpy_get():
    with boll_jpy_lock:
        if not boll_jpy_output["data"]:
            raise HTTPException(status_code=503, detail="Data not ready")
        return boll_jpy_output

# --- MA Gen ---

@app.get("/ma-gen/signals")
def ma_gen_get():
    with ma_gen_lock:
        return {"status": "success", "data": ma_gen_results}

# --- MA JPY ---

@app.get("/ma-jpy/signals")
def ma_jpy_get():
    with ma_jpy_lock:
        return {"status": "success", "data": ma_jpy_results}

# ==============================================================
# ENTRYPOINT
# ==============================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

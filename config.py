import os
from pathlib import Path

# Load a simple .env file without external dependencies
def load_env_file(path=".env"):
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        name = name.strip()
        value = value.strip()
        if (
            len(value) >= 2
            and ((value[0] == '"' and value[-1] == '"')
                 or (value[0] == "'" and value[-1] == "'"))
        ):
            value = value[1:-1]
        if name and name not in os.environ:
            os.environ[name] = value

load_env_file()


def get_env(name, default=None):
    value = os.getenv(name, default)
    return value


def parse_comma_list(env_name, default=""):
    value = get_env(env_name, default)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


DEFAULT_LOGIN = get_env("MT5_LOGIN", "128074421")
DEFAULT_PASSWORD = get_env("MT5_PASSWORD", "Pradip1999@")
DEFAULT_SERVER = get_env("MT5_SERVER", "Exness-MT5Real7")

BASE_URL = get_env("ORIVIS_BASE_URL", "http://217.154.154.252:8000").rstrip("/")
COMBINED_API_URL = get_env("COMBINED_API_URL", BASE_URL).rstrip("/")

ROUTE_MAP = {
    "/health": f"{BASE_URL}/health",
    "/fib/signal": f"{BASE_URL}/fib/signal",
    "/rsi/rsi": f"{BASE_URL}/rsi/rsi",
    "/rsi/rsi-ob-os": f"{BASE_URL}/rsi/rsi-ob-os",
    "/ma/signals": f"{BASE_URL}/ma/signals",
    "/probability/score": f"{BASE_URL}/probability/score",
}

FIB_GEN_SYMBOLS = parse_comma_list(
    "FIB_GEN_SYMBOLS",
    "EURUSDm,GBPUSDm,USDCHFm,EURGBPm,EURCHFm,GBPCHFm"
)

FIB_JPY_SYMBOLS = parse_comma_list(
    "FIB_JPY_SYMBOLS",
    "USDJPYm,GBPJPYm,CHFJPYm,EURJPYm"
)

TIMEFRAMES = parse_comma_list("TIMEFRAMES", "5m,15m,1h,1d")

FIB_KEYS = ["Fib1", "Fib2", "Fib3", "Fib4", "Fib5"]


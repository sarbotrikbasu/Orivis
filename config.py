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


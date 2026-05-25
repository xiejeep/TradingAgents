import logging
import os
import time

import pandas as pd
from .config import get_config
from .utils import safe_ticker_component

logger = logging.getLogger(__name__)

_COLUMN_MAP = {
    "日期": "Date",
    "开盘": "Open",
    "收盘": "Close",
    "最高": "High",
    "最低": "Low",
    "成交量": "Volume",
}


def akshare_retry(func, max_retries=2, base_delay=3.0):
    """Execute an akshare call with exponential backoff on connection errors.

    akshare accesses eastmoney.com through the system proxy. When the proxy
    is intermittently unavailable, this wrapper retries with backoff so the
    LLM agent doesn't need to re-invoke the tool manually.
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "AKShare network error (attempt %d/%d), retrying in %.0fs: %s",
                    attempt + 1, max_retries, delay, e,
                )
                time.sleep(delay)
    raise last_error


def _detect_exchange(symbol: str) -> str:
    symbol = str(symbol).strip().zfill(6)
    first_digit = symbol[0]
    if first_digit in ("0", "2", "3"):
        return "SZ"
    if first_digit in ("6"):
        return "SH"
    if first_digit in ("4", "8", "9"):
        return "BJ"
    return "SZ"


def _clean_symbol(symbol: str) -> str:
    symbol = str(symbol).strip().upper()
    for prefix in ("SH", "SZ", "BJ", "SS"):
        if symbol.startswith(prefix):
            symbol = symbol[len(prefix):]
    for suffix in (".SZ", ".SH", ".BJ", ".SS", ".T", ".HK", ".L", ".NS", ".BO", ".TO", ".AX"):
        if symbol.endswith(suffix):
            symbol = symbol[:-len(suffix)]
    if not symbol.isdigit() or len(symbol) != 6:
        raise ValueError(
            f"AKShare requires a 6-digit China A-share stock code, got '{symbol.strip()}'."
        )
    return symbol


def _to_exchange_symbol(symbol: str) -> str:
    code = _clean_symbol(symbol)
    exchange = _detect_exchange(code)
    return f"{exchange}{code}"


def _clean_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    data = data.rename(columns=_COLUMN_MAP)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date"])
    price_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in data.columns]
    data[price_cols] = data[price_cols].apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=["Close"])
    data[price_cols] = data[price_cols].ffill().bfill()
    return data


def load_ohlcv_akshare(symbol: str, curr_date: str) -> pd.DataFrame:
    import akshare as ak

    safe_symbol = safe_ticker_component(symbol)
    code = _clean_symbol(symbol)
    config = get_config()
    curr_date_dt = pd.to_datetime(curr_date)

    today_date = pd.Timestamp.today()
    start_date = today_date - pd.DateOffset(years=5)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = today_date.strftime("%Y-%m-%d")

    os.makedirs(config["data_cache_dir"], exist_ok=True)
    data_file = os.path.join(
        config["data_cache_dir"],
        f"{safe_symbol}-akshare-data-{start_str}-{end_str}.csv",
    )

    if os.path.exists(data_file):
        data = pd.read_csv(data_file, on_bad_lines="skip", encoding="utf-8")
    else:
        start_fmt = start_date.strftime("%Y%m%d")
        end_fmt = today_date.strftime("%Y%m%d")
        data = akshare_retry(lambda: ak.stock_zh_a_hist(
            symbol=code, period="daily",
            start_date=start_fmt, end_date=end_fmt,
            adjust="qfq",
        ))
        data.to_csv(data_file, index=False, encoding="utf-8")

    data = _clean_dataframe(data)

    keep_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    data = data[[c for c in keep_cols if c in data.columns]]

    data = data[data["Date"] <= curr_date_dt]
    return data

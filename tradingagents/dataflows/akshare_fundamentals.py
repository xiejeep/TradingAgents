from datetime import datetime

from .akshare_common import _clean_symbol, _to_exchange_symbol, akshare_retry

import akshare as ak


def get_fundamentals(ticker: str, curr_date: str = None) -> str:
    code = _clean_symbol(ticker)

    info = akshare_retry(lambda: ak.stock_individual_info_em(symbol=code))

    if info is None or info.empty:
        return f"No fundamentals data found for symbol '{code}'"

    info_dict = {}
    for _, row in info.iterrows():
        info_dict[str(row["item"])] = row["value"]

    lines = [
        f"Name: {info_dict.get('股票简称', 'N/A')}",
        f"Code: {info_dict.get('股票代码', code)}",
        f"Industry: {info_dict.get('行业', 'N/A')}",
        f"Listed Date: {info_dict.get('上市时间', 'N/A')}",
        f"Total Shares: {info_dict.get('总股本', 'N/A')}",
        f"Circulating Shares: {info_dict.get('流通股', 'N/A')}",
        f"Total Market Cap: {info_dict.get('总市值', 'N/A')}",
        f"Circulating Market Cap: {info_dict.get('流通市值', 'N/A')}",
        f"Latest Price: {info_dict.get('最新', 'N/A')}",
    ]

    header = f"# Company Fundamentals for {code}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"# Source: akshare (East Money)\n\n"

    return header + "\n".join(lines)


def _get_financial_data(symbol: str, freq: str, curr_date: str, fetch_fn, label: str) -> str:
    exchange_symbol = _to_exchange_symbol(symbol)
    freq = freq.lower() if freq else "quarterly"

    try:
        data = fetch_fn(symbol=exchange_symbol)
    except Exception as e:
        return f"Error retrieving {label} for {exchange_symbol}: {str(e)}"

    if data is None or data.empty:
        return f"No {label} data found for symbol '{exchange_symbol}'"

    for date_col in ["REPORT_DATE", "报告期"]:
        if date_col in data.columns:
            data[date_col] = data[date_col].astype(str)
            break

    if curr_date:
        try:
            for date_col in data.columns:
                col_str = data[date_col].astype(str)
                if col_str.str.match(r"^\d{4}-\d{2}-\d{2}").all():
                    mask = col_str <= curr_date
                    if mask.any():
                        data = data[mask]
                        break
        except Exception:
            pass

    csv_string = data.to_csv(index=False)

    header = f"# {label} for {exchange_symbol}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"# Source: akshare (East Money)\n\n"

    return header + csv_string


def get_balance_sheet(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    import akshare as ak

    return _get_financial_data(
        ticker, freq, curr_date,
        ak.stock_balance_sheet_by_report_em,
        "Balance Sheet",
    )


def get_cashflow(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    import akshare as ak

    return _get_financial_data(
        ticker, freq, curr_date,
        ak.stock_cash_flow_sheet_by_report_em,
        "Cash Flow Statement",
    )


def get_income_statement(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    import akshare as ak

    return _get_financial_data(
        ticker, freq, curr_date,
        ak.stock_profit_sheet_by_report_em,
        "Income Statement",
    )

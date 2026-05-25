from datetime import datetime
from typing import Optional

from .akshare_common import _clean_symbol
from .config import get_config


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    import akshare as ak

    code = _clean_symbol(ticker)

    try:
        news = ak.stock_news_em(symbol=code)
    except Exception as e:
        return f"Error fetching news for {code} from akshare: {str(e)}"

    if news is None or news.empty:
        return f"No news found for {code}"

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    article_limit = get_config().get("news_article_limit", 20)

    news_str = ""
    filtered_count = 0

    for _, row in news.iterrows():
        if filtered_count >= article_limit:
            break

        pub_time_str = str(row.get("发布时间", ""))
        try:
            pub_dt = datetime.strptime(pub_time_str[:10], "%Y-%m-%d")
            if not (start_dt <= pub_dt <= end_dt):
                continue
        except (ValueError, IndexError):
            pass

        title = row.get("新闻标题", "No title")
        content = row.get("新闻内容", "")
        source = row.get("文章来源", "Unknown")
        link = row.get("新闻链接", "")

        news_str += f"### {title} (source: {source})\n"
        if content:
            news_str += f"{content}\n"
        if link:
            news_str += f"Link: {link}\n"
        news_str += "\n"
        filtered_count += 1

    if filtered_count == 0:
        return f"No news found for {code} between {start_date} and {end_date}"

    return f"## {code} News, from {start_date} to {end_date}:\n\n{news_str}"


def get_global_news(
    curr_date: str,
    look_back_days: Optional[int] = None,
    limit: Optional[int] = None,
) -> str:
    import akshare as ak

    config = get_config()
    if look_back_days is None:
        look_back_days = config.get("global_news_lookback_days", 7)
    if limit is None:
        limit = config.get("global_news_article_limit", 10)

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")

    try:
        raw_news = ak.stock_info_global_ths()
    except Exception as e:
        return f"Error fetching global news from akshare: {str(e)}"

    if raw_news is None or raw_news.empty:
        return f"No global news found for {curr_date}"

    news_str = ""
    count = 0

    for _, row in raw_news.iterrows():
        if count >= limit:
            break

        pub_time_str = str(row.get("发布时间", ""))
        try:
            pub_dt = datetime.strptime(pub_time_str[:10], "%Y-%m-%d")
            days_diff = (curr_dt - pub_dt).days
            if days_diff > look_back_days:
                continue
        except (ValueError, IndexError):
            pass

        title = row.get("标题", "No title")
        content = row.get("内容", "")
        link = row.get("链接", "")

        news_str += f"### {title}\n"
        if content:
            news_str += f"{content}\n"
        if link:
            news_str += f"Link: {link}\n"
        news_str += "\n"
        count += 1

    if count == 0:
        return f"No global news found within {look_back_days} days of {curr_date}"

    return f"## Global Market News (akshare), past {look_back_days} days:\n\n{news_str}"


def get_insider_transactions(ticker: str) -> str:
    import akshare as ak

    code = _clean_symbol(ticker)

    try:
        data = ak.stock_dzjy_mrmx(
            symbol="A股",
            start_date=datetime.now().strftime("%Y%m%d"),
            end_date=datetime.now().strftime("%Y%m%d"),
        )
    except Exception as e:
        return f"Error fetching block trade data from akshare: {str(e)}"

    if data is None or data.empty:
        return f"No insider/block trade data available for {code}"

    if "证券代码" in data.columns:
        data = data[data["证券代码"].astype(str).str.strip() == code]

    if data.empty:
        return f"No insider/block trade data available for {code} on recent trading days"

    csv_string = data.to_csv(index=False)

    header = f"# Block Trade / Insider Transaction data for {code}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"# Source: akshare (East Money)\n\n"

    return header + csv_string

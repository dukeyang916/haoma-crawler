"""
Scrape the双色球（SSQ） historical draw records from the official
China Welfare Lottery site.

The public endpoint used here is the same one that backs the page at
https://www.cwl.gov.cn/ygkj/wqkjgg/ssq/.
"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import requests
import pandas as pd

API_URL = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


@dataclass
class LotteryDraw:
    issue: str
    draw_date: str
    red_numbers: List[str]
    blue_numbers: List[str]
    sales: str
    pool_money: str
    prize_details: str
    details_link: str

    @classmethod
    def from_api_payload(cls, payload: Dict[str, Any]) -> "LotteryDraw":
        issue = str(payload.get("code", ""))
        draw_date = str(payload.get("date", ""))
        red_numbers = payload.get("red", "").split(",") if payload.get("red") else []
        blue_numbers = [b for b in payload.get("blue", "").split(",") if b]
        sales = str(payload.get("sales", ""))
        pool_money = str(payload.get("poolmoney", ""))
        prize_details = str(payload.get("content", ""))
        details_link = str(payload.get("detailsLink", ""))
        if details_link and not details_link.startswith("http"):
            details_link = "https://www.cwl.gov.cn" + details_link

        return cls(
            issue=issue,
            draw_date=draw_date,
            red_numbers=[n.strip() for n in red_numbers if n.strip()],
            blue_numbers=[n.strip() for n in blue_numbers if n.strip()],
            sales=sales,
            pool_money=pool_money,
            prize_details=prize_details,
            details_link=details_link,
        )


def fetch_draws(issue_count: int = 30, page_no: int = 1) -> List[LotteryDraw]:
    """Fetch a single page of historical SSQ draw records.

    Args:
        issue_count: How many results to fetch for the page (the upstream API allows up to 30 at a time).
        page_no: The page number to retrieve.
    """
    params = {
        "name": "ssq",
        "issueCount": str(issue_count),
        "issueStart": "",
        "issueEnd": "",
        "dayStart": "",
        "dayEnd": "",
        "pageNo": str(page_no),
    }
    response = requests.get(API_URL, params=params, headers=DEFAULT_HEADERS, timeout=15)
    response.raise_for_status()
    payload = response.json()

    # The API sometimes wraps results in different keys; normalize them here.
    possible_lists = [
        payload.get("result"),
        payload.get("list"),
        payload.get("data"),
    ]
    records: List[Dict[str, Any]] = []
    for candidate in possible_lists:
        if isinstance(candidate, list):
            records = candidate
            break
        if isinstance(candidate, dict):
            if "list" in candidate and isinstance(candidate["list"], list):
                records = candidate["list"]
                break
            if "data" in candidate and isinstance(candidate["data"], list):
                records = candidate["data"]
                break
    if not records:
        raise ValueError("未能从返回值中解析到开奖数据，请检查 API 响应格式。")

    return [LotteryDraw.from_api_payload(item) for item in records]


def fetch_all_draws(max_pages: int = 60, page_size: int = 30) -> List[LotteryDraw]:
    """Fetch all paginated SSQ draw records (最多 60 页，每页 30 期)."""

    all_draws: List[LotteryDraw] = []
    seen_issues = set()

    for page_no in range(1, max_pages + 1):
        page_draws = fetch_draws(issue_count=page_size, page_no=page_no)
        if not page_draws:
            break

        for draw in page_draws:
            if draw.issue not in seen_issues:
                all_draws.append(draw)
                seen_issues.add(draw.issue)

        if len(page_draws) < page_size:
            # Reached the final partial page.
            break

    if not all_draws:
        raise ValueError("未能抓取到任何双色球开奖数据，请检查网络或 API 参数。")

    return all_draws


def export_to_excel(draws: List[LotteryDraw], file_path: str = "ssq_history.xlsx") -> None:
    df = pd.DataFrame([asdict(draw) for draw in draws])
    df.to_excel(file_path, index=False)


def export_to_csv(draws: List[LotteryDraw], file_path: str = "ssq_history.csv") -> None:
    df = pd.DataFrame([asdict(draw) for draw in draws])
    df.to_csv(file_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    draws = fetch_all_draws(max_pages=60, page_size=30)
    export_to_excel(draws)
    export_to_csv(draws)
    print(f"已保存 {len(draws)} 期双色球数据到 ssq_history.xlsx 和 ssq_history.csv")

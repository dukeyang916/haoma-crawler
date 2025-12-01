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


def fetch_draws(issue_count: int = 30) -> List[LotteryDraw]:
    """Fetch historical SSQ draw records.

    Args:
        issue_count: How many recent issues to fetch. The upstream API allows up to 30 at a time.
    """
    params = {
        "name": "ssq",
        "issueCount": str(issue_count),
        "issueStart": "",
        "issueEnd": "",
        "dayStart": "",
        "dayEnd": "",
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


def export_to_excel(draws: List[LotteryDraw], file_path: str = "ssq_history.xlsx") -> None:
    df = pd.DataFrame([asdict(draw) for draw in draws])
    df.to_excel(file_path, index=False)


def export_to_csv(draws: List[LotteryDraw], file_path: str = "ssq_history.csv") -> None:
    df = pd.DataFrame([asdict(draw) for draw in draws])
    df.to_csv(file_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    draws = fetch_draws(issue_count=30)
    export_to_excel(draws)
    export_to_csv(draws)
    print(f"已保存 {len(draws)} 期双色球数据到 ssq_history.xlsx 和 ssq_history.csv")

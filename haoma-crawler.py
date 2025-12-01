from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import pandas as pd
import time

# 1）城市：左边是 dis 参数，右边是中文名（用于文件名）
CITY_LIST = {
    #"shenzhen": "深圳",
    #"guangzhou": "广州",
    #"dongguan": "东莞",
    #"foshan": "佛山",
    #"zhongshan": "中山",
    #"zhuhai": "珠海",

    #"huizhou": "惠州",
    #"zhaoqing": "肇庆",
    #"yangjiang": "阳江",
    #"shanwei": "汕尾",
    #"meizhou": "梅州",
    #"yunfu": "云浮",
    #"qingyuan": "清远",
    #"zhanjiang": "湛江",
    #"maoming": "茂名",
    #"shantou": "汕头",
    #"chaozhou": "潮州",
    #"heyuan": "河源",
    #"jiangmen": "江门",
    #"shaoguan": "韶关",
    #"jieyang": "揭阳",

    "chongqing": "重庆",
    #"guangan": "广安",
    #"wuhan": "武汉",
    #"jingzhou": "荆州",
    #"ningbo": "宁波",
    #"putian": "莆田",
    #"zhangzhou": "漳州",
    #"hangzhou": "杭州",
    #"lishui": "丽水",
    #"jinhua": "金华",
    #"jiaxing": "嘉兴",
    #"nanjing": "南京",
    #"suzhou": "苏州",
    #"wuxi": "无锡",
    #"nantong": "南通",
    #"changzhou": "常州",
    #"xuzhou": "徐州",
    #"yangzhou": "扬州",
    #"yancheng": "盐城",
    #"taizhou": "泰州",
    #"zhenjiang": "镇江",
    #"huaian": "淮安",
    #"suqian": "宿迁",
    #"lianyungang": "连云港"
   }


# 2）运营商：key 是 opt 参数，value 是中文名
#    "" 代表不限运营商（即页面上“不限”）
OPERATOR_LIST = {
#    "":  "全部运营商",  # 不带 opt 参数
    "yd": "移动",
#    "lt": "联通",
#    "dx": "电信",
#    "gd": "广电"
}

MAX_PAGE = 15  # 每个城市 / 运营商 组合最多翻多少页，调大调小都行


def scrape_numbers():
    all_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 双重循环：城市 × 运营商
        for dis, city_cn in CITY_LIST.items():
            for opt_code, op_cn in OPERATOR_LIST.items():
                print(f"\n========== 城市：{city_cn}（dis={dis}），运营商：{op_cn}（opt={opt_code or '无'}） ==========")

                for page_no in range(1, MAX_PAGE + 1):
                    # 组 URL：有 opt 就带 opt，没有就不带
                    if opt_code:
                        url = f"https://hot.haoma.com/xuanhao?dis={dis}&opt={opt_code}&page={page_no}"
                    else:
                        url = f"https://hot.haoma.com/xuanhao?dis={dis}&page={page_no}"

                    print(f"正在抓取第 {page_no} 页: {url}")
                    page.goto(url, wait_until="networkidle")
                    page.wait_for_timeout(1000)

                    html = page.content()
                    soup = BeautifulSoup(html, "lxml")

                    # 每个号码卡片（外层容器）
                    cards = soup.find_all("div", class_="content")
                    print(f"  本页找到号码卡片数量: {len(cards)}")

                    # 没数据就提前结束当前「城市+运营商」的翻页
                    if not cards:
                        print("  本页无数据，提前结束该组合翻页。")
                        break

                    for card in cards:
                        # 1️⃣ 号码在 div.num-hd 里的 span.number
                        num_hd = card.find("div", class_="num-hd")
                        if not num_hd:
                            continue

                        digit_spans = num_hd.find_all("span", class_="number")
                        digits = "".join(span.get_text(strip=True) for span in digit_spans)
                        if len(digits) < 11:
                            continue
                        number = digits[-11:]

                        # 2️⃣ 整块文本 → 解析运营商 / 标签 / 价格
                        text_all = card.get_text(separator=" ", strip=True)

                        # 去掉前面长串数字
                        text_no_num = re.sub(r'(?:\d\s*){7,}', ' ', text_all).strip()

                        # 去掉尾部“预约 / 取消 / 收藏 / 微信扫码测吉凶”
                        for kw in ["预约", "取消", "收藏", "微信扫码测吉凶"]:
                            idx = text_no_num.find(kw)
                            if idx != -1:
                                text_no_num = text_no_num[:idx]
                        text_no_num = text_no_num.strip()

                        tokens = text_no_num.split()
                        if not tokens:
                            continue

                        # 卡片里显示的归属地+运营商，例如 “上海移动”
                        carrier = tokens[0]

                        tag_tokens = []
                        price = "0"
                        include_fee = "0"

                        for t in tokens[1:]:
                            if re.fullmatch(r"\d+", t) and price == "0":
                                price = t
                                continue
                            if "含话费" in t:
                                m = re.search(r"含话费(\d+)元", t)
                                if m:
                                    include_fee = m.group(1)
                                continue
                            tag_tokens.append(t)

                        tag = " ".join(tag_tokens)

                        # 详情链接（预约按钮）
                        detail_url = ""
                        order_link = card.find("a", href=re.compile("order"))
                        if order_link:
                            detail_url = order_link.get("href", "")
                            if detail_url and not detail_url.startswith("http"):
                                detail_url = "https://hot.haoma.com/" + detail_url.lstrip("/")

                        # 关键：保存 “城市页面” 和 “运营商页面”
                        all_data.append({
                            "city_page": city_cn,        # 地区推荐城市
                            "operator_page": op_cn,      # 页面上选的运营商
                            "number": number,
                            "carrier": carrier,          # 号码本身的归属运营商（例如“上海移动”）
                            "tag": tag,
                            "price": price,
                            "include_fee": include_fee,
                            "detail_url": detail_url,
                        })

                    time.sleep(0.3)

        browser.close()

    # -------------------------
    # 整体数据 & 按城市+运营商拆表
    # -------------------------
    df = pd.DataFrame(all_data)
    df.drop_duplicates(subset=["city_page", "operator_page", "number"], inplace=True)

    # ① 全部数据一份
    df.to_excel("all_numbers_multi_city_op.xlsx", index=False)
    print(f"\n全部组合合计：{len(df)} 条，已保存到 all_numbers_multi_city_op.xlsx")

    # ② 按“城市 + 运营商”拆表（不拆“全部运营商”也可以自己改）
    for (city_cn, op_cn), df_group in df.groupby(["city_page", "operator_page"]):
        # 如果你不想导出“全部运营商”，可以跳过：
        # if op_cn == "全部运营商":
        #     continue

        safe_op_name = op_cn.replace(" ", "")
        file_name = f"{city_cn}_{safe_op_name}_numbers.xlsx"
        df_group.to_excel(file_name, index=False)
        print(f"{city_cn} - {op_cn}：{len(df_group)} 条，已保存到 {file_name}")


if __name__ == "__main__":
    scrape_numbers()

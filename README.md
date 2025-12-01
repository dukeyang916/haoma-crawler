# 号码之家多城市多运营商爬虫

这是一个使用 **Playwright + BeautifulSoup + Pandas** 开发的自动化爬虫脚本，  
用于从 [hot.haoma.com](https://hot.haoma.com) 批量抓取手机号码数据，并按「城市 + 运营商」自动分类导出 Excel 号池。

> ⚠ 本项目仅用于个人学习和技术研究，请勿用于任何违法用途。请遵守网站的 robots & 相关法律法规。

---

## ✨ 功能简介

- 支持一次配置多个城市（`dis=` 参数）
- 支持多个运营商筛选（移动 / 联通 / 电信 / 广电 / 不限）
- 自动翻页（可设置最大页数）
- 自动解析以下信息：
  - 号码
  - 归属地 + 运营商（如“上海移动”）
  - 售价
  - 含话费金额
  - 标签（靓号 / 情侣号 / 生日号等）
  - 预约链接
- 自动生成多个 Excel：
  - `all_numbers_multi_city_op.xlsx`（总汇总）
  - `{城市}_{运营商}_numbers.xlsx`

---

## 📦 环境准备

### 1. 安装 Python

建议 Python 3.10+  
下载地址：https://www.python.org/downloads/

安装时记得勾选 **Add Python to PATH**。

---

### 2. （可选）创建虚拟环境

```bash
cd C:\Users\duke\Desktop\haoma-crawler
python -m venv venv
venv\Scripts\activate
激活后命令行前面会出现 (venv)。

3. 安装依赖
bash
复制代码
pip install -r requirements.txt
安装 Playwright 浏览器内核：

bash
复制代码
playwright install
🚀 运行脚本
在项目根目录执行：

bash
复制代码
python haoma_crawler.py
脚本会自动：

1.遍历 CITY_LIST 中的城市

2.遍历 OPERATOR_LIST 中的运营商

3.翻页抓取号码

4.导出 Excel 文件

⚙ 配置说明
项目核心配置放在脚本顶部。

1️⃣ 城市配置（CITY_LIST）
python
复制代码
CITY_LIST = {
    "shenzhen": "深圳",
    "guangzhou": "广州",
    "dongguan": "东莞",
    # ...
}
左侧 key = URL 中的 dis= 参数

右侧 value = 中文名，用于 Excel 文件名

2️⃣ 运营商配置（OPERATOR_LIST）
python
复制代码
OPERATOR_LIST = {
    "":  "全部运营商",  # 表示“不限”，不带 opt 参数
    "yd": "移动",
    "lt": "联通",
    "dx": "电信",
    "gd": "广电",
}
如果你只想抓移动+联通，可以：

python
复制代码
OPERATOR_LIST = {
    "yd": "移动",
    "lt": "联通",
}
📁 requirements.txt
确保内容如下：

nginx
复制代码
playwright
beautifulsoup4
lxml
pandas
openpyxl
🧰 Git & GitHub 教程
初始化仓库
bash
复制代码
cd C:\Users\duke\Desktop\haoma-crawler
git init
第一次推送到 GitHub
bash
复制代码
git add .
git commit -m "first upload"
git branch -M main
git remote add origin https://github.com/你的用户名/haoma-crawler.git
git push -u origin main
后续更新
bash
复制代码
git add .
git commit -m "update crawler logic"
git push
📜 License
本项目采用 MIT License（如需可修改）。


import time

import requests
import streamlit as st


# 1. 定义自定义异常，消除 "Create your own exception" 警告
class BitcoinAPIError(Exception):
    """自定义的比特币 API 异常"""


@st.cache_data(ttl=60, show_spinner="正在获取最新比特币价格...")
def fetch_bitcoin_data():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"}
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BTC-Streamlit-App",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        btc_data = data.get("bitcoin")

        if not btc_data or "usd" not in btc_data:
            return None

        current_price = btc_data["usd"]
        change_percentage_24h = btc_data.get("usd_24h_change", 0)

        denominator = 1 + change_percentage_24h / 100
        if denominator != 0:
            price_24h_ago = current_price / denominator
            change_amount_24h = current_price - price_24h_ago
        else:
            change_amount_24h = current_price

        return {
            "current_price": current_price,
            "change_percentage_24h": change_percentage_24h,
            "change_amount_24h": change_amount_24h,
            "timestamp": time.time(),
        }

    except requests.exceptions.Timeout:
        raise BitcoinAPIError("请求超时，请检查网络连接后重试。")

    except requests.exceptions.ConnectionError:
        raise BitcoinAPIError("网络连接异常，无法访问 API 服务。")

    except requests.exceptions.HTTPError as e:
        # 2. 增加 e.response 的 None 检查，消除红色警告
        if e.response is not None:
            if e.response.status_code == 429:
                raise BitcoinAPIError("API 请求频率超限，请稍后重试。")
            elif e.response.status_code == 403:
                raise BitcoinAPIError("被 API 网关拦截，请检查请求头或网络环境。")
        raise BitcoinAPIError(f"HTTP 错误: {e}")

    except Exception as e:
        # 3. 盲目捕获兜底：使用 from e 保留原始错误堆栈，并抛出统一的自定义异常
        # 注意：如果是为了防止页面崩溃给用户看友好提示，这种盲捕获在 UI 层是可以接受的
        raise BitcoinAPIError(f"获取数据时发生意外错误: {e}") from e


# ==========================================
# 2. 界面展示与交互控制模块
# ==========================================


def main():
    st.set_page_config(page_title="比特币实时价格", page_icon="₿", layout="wide")

    # 更加精简的隐藏页脚样式
    hide_style = (
        "<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>"
    )
    st.markdown(hide_style, unsafe_allow_html=True)

    st.title("₿ 比特币实时价格监控")
    st.caption("数据来源: CoinGecko | 自动刷新间隔: 60秒")

    # 刷新按钮 - 精确清除特定函数缓存
    if st.button("🔄 手动刷新数据", use_container_width=True):
        fetch_bitcoin_data.clear()

    # 获取数据与 UI 级别异常处理解耦
    btc_data = None
    try:
        btc_data = fetch_bitcoin_data()
    except Exception as e:
        st.error(str(e))

    if btc_data:
        current_price = btc_data["current_price"]
        change_pct = btc_data["change_percentage_24h"]
        change_amt = btc_data["change_amount_24h"]

        # 使用原生 st.metric 简化代码，并利用其自带的红涨绿跌逻辑
        st.metric(
            label="当前价格 (BTC/USD)",
            value=f"${current_price:,.2f}",
            label_visibility="visible",
        )

        # 分两列展示涨跌额和涨跌幅
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="24h 涨跌额 (USD)",
                value=f"${change_amt:,.2f}",
                delta=f"{change_pct:.2f}%",  # delta会根据正负自动变红绿
            )

        with col2:
            st.metric(
                label="24h 涨跌幅 (%)",
                value=f"{change_pct:.2f}%",
                delta=f"${change_amt:,.2f}",
            )

        update_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(btc_data["timestamp"])
        )
        st.info(f"⏱️ 数据更新时间: {update_time}", icon="ℹ️")

    else:
        if btc_data is None:  # 仅在网络正常但数据异常时显示
            st.warning("未能加载比特币价格数据，请稍后点击刷新重试。")


if __name__ == "__main__":
    main()

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="專業級股票分析儀", layout="wide")

# --- 1. 資料結構 ---
STOCK_CATEGORIES = {
    "上市熱門": [{'ticker': '2330.TW', 'name': '台積電'}, {'ticker': '2317.TW', 'name': '鴻海'}, {'ticker': '2454.TW', 'name': '聯發科'}],
    "熱門 ETF": [{'ticker': '0050.TW', 'name': '元大50'}, {'ticker': '0056.TW', 'name': '元大高股息'}],
    "經典美股": [{'ticker': 'NVDA', 'name': '輝達'}, {'ticker': 'AAPL', 'name': '蘋果'}]
}

# --- 2. 側邊欄控制 ---
st.sidebar.title("控制面板")
category = st.sidebar.selectbox("分類", list(STOCK_CATEGORIES.keys()))
stock = st.sidebar.selectbox("標的", STOCK_CATEGORIES[category], format_func=lambda x: x['name'])
ticker = stock['ticker']

mode = st.sidebar.radio("數據模式", ["歷史圖表", "即時走勢"])

if mode == "歷史圖表":
    time_frame = st.sidebar.selectbox("週期", ["D (日)", "W (週)", "M (月)"])
    period = st.sidebar.selectbox("時間範圍", ["1y", "2y", "5y", "max"])
    window = st.sidebar.slider("顯示筆數 (視窗)", 20, 500, 100)
else:
    interval = st.sidebar.selectbox("頻率", ["1m", "5m", "30m", "1h"])
    window = st.sidebar.slider("顯示筆數 (視窗)", 50, 500, 200)

# --- 3. 資料獲取與均線計算 ---
@st.cache_data(ttl=600)
def get_data(ticker, mode, interval_map=None, period=None):
    if mode == "歷史圖表":
        df = yf.Ticker(ticker).history(period=period, interval=interval_map)
    else:
        df = yf.Ticker(ticker).history(period="5d", interval=interval_map)
    
    # 均線計算 (5T, 10T, 20T)
    df['SMA5'] = ta.trend.sma_indicator(df['Close'], window=5)
    df['SMA10'] = ta.trend.sma_indicator(df['Close'], window=10)
    df['SMA20'] = ta.trend.sma_indicator(df['Close'], window=20)
    
    # 指標計算
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['Signal'] = macd.macd_signal()
    kd = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
    df['K'] = kd.stoch()
    df['D'] = kd.stoch_signal()
    return df

# 映射週期代碼
interval_map = {'D (日)': '1d', 'W (週)': '1wk', 'M (月)': '1mo'}.get(time_frame if mode=="歷史圖表" else "1d", interval if mode=="即時走勢" else "1d")
df = get_data(ticker, mode, interval_map, period if mode=="歷史圖表" else None)
df_plot = df.tail(window)

# --- 4. 繪圖 ---
st.title(f"📊 {stock['name']} 深度分析")
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.08, row_heights=[0.5, 0.25, 0.25])

# K線 + 均線
fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name='Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['SMA5'], name='5T', line=dict(color='orange', width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['SMA10'], name='10T', line=dict(color='yellow', width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['SMA20'], name='20T', line=dict(color='red', width=1)), row=1, col=1)

# MACD
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MACD'], name='MACD', line=dict(color='blue')), row=2, col=1)
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Signal'], name='Signal', line=dict(color='orange')), row=2, col=1)

# KD
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['K'], name='K值', line=dict(color='purple')), row=3, col=1)
fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['D'], name='D值', line=dict(color='green')), row=3, col=1)

# 標籤設定
fig.update_layout(height=850, xaxis_rangeslider_visible=False, template="plotly_white", margin=dict(t=50, b=50))
st.plotly_chart(fig, width='stretch')

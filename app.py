import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# 1. 頁面配置
st.set_page_config(page_title="專業看盤系統", layout="wide")

# 2. CSS 精簡設定：移除白色區塊，確保文字正常顯示
st.markdown("""
    <style>
    /* 移除背景顏色，設定為純黑 */
    .stApp { background-color: #000000; }
    
    /* 確保標題正常且不被擠出 */
    h1 { color: #FFFFFF !important; font-size: 24px !important; margin-bottom: 0.5rem !important; }
    
    /* 緊湊容器，保留適當邊距防切邊 */
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Metric 優化 */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 18px !important; }
    [data-testid="stMetricLabel"] { color: #CCCCCC !important; font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 標的資料讀取
@st.cache_data
def load_stocks():
    try:
        with open('stocks.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"錯誤": [{"ticker": "^TWII", "name": "無法讀取 JSON"}]}

STOCK_CATEGORIES = load_stocks()

# 4. 圖表主題函數
def apply_black_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF", size=12),
        margin=dict(l=10, r=10, t=20, b=10),
        hovermode="x unified"
    )
    fig.update_xaxes(showspikes=True, spikecolor="white", spikethickness=1, rangebreaks=[dict(bounds=["sat", "mon"])])
    fig.update_yaxes(showspikes=True, spikecolor="white", spikethickness=1)

# 5. 控制面板與數據處理
st.sidebar.title("控制面板")
all_stocks = [s for cat in STOCK_CATEGORIES.values() for s in cat]
search = st.sidebar.text_input("🔍 搜尋標的")
if search:
    filtered = [s for s in all_stocks if search.lower() in s['name'].lower() or search.upper() in s['ticker'].upper()]
    stock = st.sidebar.selectbox("搜尋結果", filtered, format_func=lambda x: f"{x['name']} ({x['ticker']})") if filtered else all_stocks[0]
else:
    category = st.sidebar.selectbox("選擇分類", list(STOCK_CATEGORIES.keys()))
    stock = st.sidebar.selectbox("選擇標的", STOCK_CATEGORIES[category], format_func=lambda x: x['name'])

ticker, time_frame = stock['ticker'], st.sidebar.selectbox("週期", ["日線 (1d)", "週線 (1wk)", "月線 (1mo)"])
interval_map = {'日線 (1d)': '1d', '週線 (1wk)': '1wk', '月線 (1mo)': '1mo'}[time_frame]
window = st.sidebar.slider("視窗筆數", 20, 500, 100)
opt_top, opt_bot = st.sidebar.selectbox("右上指標", ["MACD", "KD", "VOL", "無"]), st.sidebar.selectbox("右下指標", ["KD", "MACD", "VOL", "無"])

@st.cache_data(ttl=600)
def get_data(ticker, interval):
    df = yf.Ticker(ticker).history(period="5y", interval=interval)
    df['SMA5'] = ta.trend.sma_indicator(df['Close'], window=5)
    macd = ta.trend.MACD(df['Close'])
    df['MACD'], df['Signal'] = macd.macd(), macd.macd_signal()
    kd = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
    df['K'], df['D'] = kd.stoch(), kd.stoch_signal()
    return df

df = get_data(ticker, interval_map).tail(window)
latest = df.iloc[-1]

# 6. 主頁面繪圖
st.title(f"📊 {stock['name']} ({ticker})")

m1, m2, m3, m4 = st.columns(4)
m1.metric("價格", f"{latest['Close']:.2f}")
m2.metric("開盤", f"{latest['Open']:.2f}")
m3.metric("最高", f"{latest['High']:.2f}")
m4.metric("最低", f"{latest['Low']:.2f}")

col_left, col_right = st.columns([2, 1])
chart_config = {'displayModeBar': False}

with col_left:
    fig_main = go.Figure()
    fig_main.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#FF3E3E', decreasing_line_color='#00FF7F'))
    fig_main.add_trace(go.Scatter(x=df.index, y=df['SMA5'], name='SMA5', line=dict(width=2)))
    apply_black_theme(fig_main)
    fig_main.update_layout(height=450, xaxis=dict(matches='x'))
    st.plotly_chart(fig_main, width="stretch", config=chart_config)

with col_right:
    fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)
    def add_tech(fig, opt, row):
        if opt == "MACD":
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='DIF', line=dict(color='yellow', width=2)), row=row, col=1)
            fig.add_trace(go.Bar(x=df.index, y=df['MACD']-df['Signal'], name='Hist', marker_color='#FF3E3E'), row=row, col=1)
        elif opt == "KD":
            fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='K值', line=dict(color='magenta', width=2)), row=row, col=1)
    
    add_tech(fig_tech, opt_top, 1)
    add_tech(fig_tech, opt_bot, 2)
    apply_black_theme(fig_tech)
    fig_tech.update_layout(height=450, showlegend=False)
    st.plotly_chart(fig_tech, width="stretch", config=chart_config)

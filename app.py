import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# 1. 頁面配置
st.set_page_config(page_title="專業看盤系統", layout="wide")

# CSS 強制覆蓋：使用高對比度純白色文字，並優化 Metric 顯示
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    /* 強制將 Metric 數值設為純白高對比 */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 32px !important; }
    [data-testid="stMetricLabel"] { color: #CCCCCC !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 標的資料 (讀取 JSON)
@st.cache_data
def load_stocks():
    try:
        with open('stocks.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"錯誤": [{"ticker": "^TWII", "name": "無法讀取 JSON"}]}

STOCK_CATEGORIES = load_stocks()

# 3. 核心函數
def apply_black_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF", size=18),
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified"
    )
    fig.update_xaxes(
        gridcolor="#333333", 
        tickfont=dict(size=16), 
        rangebreaks=[dict(bounds=["sat", "mon"])],
        showspikes=True, spikecolor="white", spikethickness=1
    )
    fig.update_yaxes(
        gridcolor="#333333", 
        tickfont=dict(size=16),
        showspikes=True, spikecolor="white", spikethickness=1
    )

# 4. 控制面板 (加入網路搜尋功能)
st.sidebar.title("控制面板")

# 建立所有標的扁平化清單供搜尋
all_stocks = []
for cat in STOCK_CATEGORIES.values():
    all_stocks.extend(cat)

search = st.sidebar.text_input("🔍 搜尋標的 (輸入代號/名稱)")
if search:
    # 嘗試先從本地搜尋
    filtered = [s for s in all_stocks if search.lower() in s['name'].lower() or search.upper() in s['ticker'].upper()]
    
    if filtered:
        stock = st.sidebar.selectbox("搜尋結果", filtered, format_func=lambda x: f"{x['name']} ({x['ticker']})")
    else:
        # 如果本地找不到，嘗試網路搜尋
        try:
            ticker_obj = yf.Ticker(search.upper())
            info = ticker_obj.info
            if 'longName' in info:
                stock = {'ticker': search.upper(), 'name': info['longName']}
                st.sidebar.success(f"網路搜尋: {info['longName']}")
            else:
                st.sidebar.error("找不到標的")
                stock = all_stocks[0] # 回退到預設
        except:
            st.sidebar.error("網路搜尋失敗")
            stock = all_stocks[0]
else:
    category = st.sidebar.selectbox("選擇分類", list(STOCK_CATEGORIES.keys()))
    stock = st.sidebar.selectbox("選擇標的", STOCK_CATEGORIES[category], format_func=lambda x: x['name'])

ticker = stock['ticker']
time_frame = st.sidebar.selectbox("時間週期", ["日線 (1d)", "週線 (1wk)", "月線 (1mo)"])
interval_map = {'日線 (1d)': '1d', '週線 (1wk)': '1wk', '月線 (1mo)': '1mo'}[time_frame]
window = st.sidebar.slider("顯示筆數 (視窗)", 20, 500, 100)
opt_top = st.sidebar.selectbox("右上指標", ["MACD", "KD", "VOL", "無"])
opt_bot = st.sidebar.selectbox("右下指標", ["KD", "MACD", "VOL", "無"])

# 5. 資料處理
@st.cache_data(ttl=600)
def get_data(ticker, interval):
    df = yf.Ticker(ticker).history(period="5y", interval=interval)
    df['SMA5'] = ta.trend.sma_indicator(df['Close'], window=5)
    df['SMA10'] = ta.trend.sma_indicator(df['Close'], window=10)
    df['SMA20'] = ta.trend.sma_indicator(df['Close'], window=20)
    macd = ta.trend.MACD(df['Close'])
    df['MACD'], df['Signal'] = macd.macd(), macd.macd_signal()
    kd = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
    df['K'], df['D'] = kd.stoch(), kd.stoch_signal()
    return df

df = get_data(ticker, interval_map).tail(window)
latest = df.iloc[-1]

# 6. 繪圖
st.title(f"📊 {stock['name']} ({ticker}) 深度分析")

# 頂部數據列
m1, m2, m3, m4 = st.columns(4)
m1.metric("當前價格", f"{latest['Close']:.2f}")
m2.metric("開盤", f"{latest['Open']:.2f}")
m3.metric("最高", f"{latest['High']:.2f}")
m4.metric("最低", f"{latest['Low']:.2f}")

col_left, col_right = st.columns([2, 1])
chart_config = {'displayModeBar': False} # 禁用縮放按鈕

with col_left:
    st.subheader("趨勢與均線")
    fig_main = go.Figure()
    fig_main.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
        name='K線', increasing_line_color='#FF3E3E', decreasing_line_color='#00FF7F',
        hovertemplate='日期: %{x|%Y-%m-%d}<br>收盤: %{close:.2f}<extra></extra>'
    ))
    for col, name in [('SMA5','5T'), ('SMA10','10T'), ('SMA20','20T')]:
        fig_main.add_trace(go.Scatter(x=df.index, y=df[col], name=name, line=dict(width=3)))
    
    apply_black_theme(fig_main)
    fig_main.update_layout(height=700, xaxis=dict(matches='x'))
    st.plotly_chart(fig_main, width="stretch", config=chart_config)

with col_right:
    st.subheader("技術分析")
    fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    
    def add_tech(fig, opt, row):
        if opt == "MACD":
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='DIF', line=dict(color='yellow', width=2)), row=row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='MACD', line=dict(color='cyan', width=2)), row=row, col=1)
            hist = df['MACD'] - df['Signal']
            fig.add_trace(go.Bar(x=df.index, y=hist, name='Hist', marker_color=['#FF3E3E' if x >= 0 else '#00FF7F' for x in hist]), row=row, col=1)
        elif opt == "KD":
            fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='K值', line=dict(color='magenta', width=2)), row=row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['D'], name='D值', line=dict(color='lime', width=2)), row=row, col=1)
        elif opt == "VOL":
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color='#888888'), row=row, col=1)

    add_tech(fig_tech, opt_top, 1)
    add_tech(fig_tech, opt_bot, 2)
    
    apply_black_theme(fig_tech)
    fig_tech.update_layout(height=700, showlegend=False)
    st.plotly_chart(fig_tech, width="stretch", config=chart_config)

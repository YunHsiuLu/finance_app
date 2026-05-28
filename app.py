import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 頁面配置
st.set_page_config(page_title="專業看盤系統", layout="wide")

# CSS 強制覆蓋
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 標的資料 (嚴格換行)
STOCK_CATEGORIES = {
    "上市熱門": [
        {'ticker': '^TWII', 'name': '台灣大盤'},
        {'ticker': '2330.TW', 'name': '台積電'},
        {'ticker': '2317.TW', 'name': '鴻海'},
        {'ticker': '2454.TW', 'name': '聯發科'},
        {'ticker': '2303.TW', 'name': '聯電'},
        {'ticker': '3034.TW', 'name': '聯詠'},
        {'ticker': '3260.TWO', 'name': '威剛'},
        {'ticker': '2603.TW', 'name': '長榮'},
        {'ticker': '2609.TW', 'name': '陽明'},
        {'ticker': '2610.TW', 'name': '華航'},
        {'ticker': '2382.TW', 'name': '廣達'},
        {'ticker': '2881.TW', 'name': '富邦金'},
        {'ticker': '3711.TW', 'name': '日月光'},
        {'ticker': '3008.TW', 'name': '大立光'},
        {'ticker': '8299.TWO', 'name': '群聯'}
    ],
    "熱門 ETF": [
        {'ticker': '^TWII', 'name': '台灣大盤'},
        {'ticker': '0050.TW', 'name': '元大50'},
        {'ticker': '0056.TW', 'name': '元大高股息'},
        {'ticker': '00878.TW', 'name': '國泰高股息'},
        {'ticker': '006208.TW', 'name': '富邦台50'},
        {'ticker': '00919.TW', 'name': '群益00919'},
        {'ticker': '00929.TW', 'name': '復華00929'},
        {'ticker': '00712.TW', 'name': '復華富時不動產'},
        {'ticker': '00713.TW', 'name': '元大00713'},
        {'ticker': '00981A.TW', 'name': '00981A'}
    ],
    "經典美股": [
        {'ticker': '^IXIC', 'name': '那斯達克'},
        {'ticker': 'TSM', 'name': '台積電ADR'},
        {'ticker': 'NVDA', 'name': '輝達 (NVDA)'},
        {'ticker': 'AMD', 'name': '超微 (AMD)'},
        {'ticker': 'INTC', 'name': '英特爾'},
        {'ticker': 'TSLA', 'name': '特斯拉'},
        {'ticker': 'AAPL', 'name': '蘋果 (AAPL)'},
        {'ticker': 'MSFT', 'name': '微軟 (MSFT)'},
        {'ticker': 'GOOGL', 'name': '谷歌 (GOOGL)'},
        {'ticker': 'QQQ', 'name': '納指100ETF'},
        {'ticker': 'SOXX', 'name': '費半半導體ETF'}
    ]
}

# 3. 核心函數
def apply_black_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#FFFFFF", size=18),
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified" # 開啟十字聯動
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

# 4. 控制面板
st.sidebar.title("控制面板")
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

# 6. 繪圖
st.title(f"📊 {stock['name']} ({ticker}) 深度分析")
col_left, col_right = st.columns([2, 1])
chart_config = {'displayModeBar': False} # 禁用縮放按鈕

with col_left:
    st.subheader("趨勢與均線")
    fig_main = go.Figure()
    fig_main.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線', increasing_line_color='#FF3E3E', decreasing_line_color='#00FF7F'))
    for col, name in [('SMA5','5T'), ('SMA10','10T'), ('SMA20','20T')]:
        fig_main.add_trace(go.Scatter(x=df.index, y=df[col], name=name, line=dict(width=3)))
    
    apply_black_theme(fig_main)
    fig_main.update_layout(height=700, xaxis=dict(matches='x')) # 鎖定座標系聯動
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

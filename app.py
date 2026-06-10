import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# 1. 頁面配置
st.set_page_config(page_title="專業看盤系統", layout="wide")

# 2. 頁面樣式
st.markdown("""
    <style>
    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"] {
        background-color: #000000;
    }

    /* Streamlit 的固定 header 會蓋住內容，背景也必須與主畫面一致。 */
    header[data-testid="stHeader"] {
        background-color: #000000;
    }

    h1 {
        color: #FFFFFF !important;
        font-size: 24px !important;
        line-height: 1.35 !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }

    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* 側邊欄改為深色底，避免標題與欄位標籤失去對比。 */
    section[data-testid="stSidebar"] {
        background-color: #151A23;
        border-right: 1px solid #303846;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #F4F7FB !important;
    }

    section[data-testid="stSidebar"] input {
        color: #FFFFFF !important;
        background-color: #242B36 !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="input"],
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        color: #FFFFFF !important;
        background-color: #242B36 !important;
        border-color: #4A5568 !important;
    }

    section[data-testid="stSidebar"] svg {
        fill: #DCE3EC !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 18px !important;
    }

    [data-testid="stMetricLabel"] {
        color: #CCCCCC !important;
        font-size: 12px !important;
    }
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
        font=dict(color="#FFFFFF", size=12, family="Arial, sans-serif"),
        margin=dict(l=10, r=10, t=20, b=10),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1B2330",
            bordercolor="#5F6B7A",
            font=dict(color="#FFFFFF", size=12)
        ),
        legend=dict(
            font=dict(color="#FFFFFF", size=12),
            bgcolor="rgba(0, 0, 0, 0.65)",
            bordercolor="#3A4554",
            borderwidth=1
        )
    )
    fig.update_xaxes(
        color="#FFFFFF",
        tickfont=dict(color="#E6EAF0", size=11),
        gridcolor="#3A3F48",
        zerolinecolor="#59616D",
        linecolor="#AAB2BD",
        showspikes=True,
        spikecolor="#FFFFFF",
        spikethickness=1,
        rangebreaks=[dict(bounds=["sat", "mon"])]
    )
    fig.update_yaxes(
        color="#FFFFFF",
        tickfont=dict(color="#E6EAF0", size=11),
        gridcolor="#3A3F48",
        zerolinecolor="#59616D",
        linecolor="#AAB2BD",
        showspikes=True,
        spikecolor="#FFFFFF",
        spikethickness=1
    )

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
    fig_tech = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=(opt_top, opt_bot)
    )

    def add_tech(fig, opt, row):
        if opt == "MACD":
            histogram = df['MACD'] - df['Signal']
            colors = ['#FF5A5F' if value >= 0 else '#00D084' for value in histogram]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MACD'],
                    name='DIF',
                    line=dict(color='#FFD54F', width=2)
                ),
                row=row,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['Signal'],
                    name='Signal',
                    line=dict(color='#4FC3F7', width=1.5)
                ),
                row=row,
                col=1
            )
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=histogram,
                    name='柱狀體',
                    marker_color=colors
                ),
                row=row,
                col=1
            )
        elif opt == "KD":
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['K'],
                    name='K值',
                    line=dict(color='#FF4DFF', width=2)
                ),
                row=row,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['D'],
                    name='D值',
                    line=dict(color='#4FC3F7', width=1.5)
                ),
                row=row,
                col=1
            )
        elif opt == "VOL":
            colors = [
                '#FF5A5F' if close >= open_price else '#00D084'
                for close, open_price in zip(df['Close'], df['Open'])
            ]
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='成交量',
                    marker_color=colors
                ),
                row=row,
                col=1
            )
    
    add_tech(fig_tech, opt_top, 1)
    add_tech(fig_tech, opt_bot, 2)
    apply_black_theme(fig_tech)
    fig_tech.update_annotations(
        font=dict(color="#FFFFFF", size=15, family="Arial, sans-serif"),
        bgcolor="#1B2330",
        bordercolor="#5F6B7A",
        borderwidth=1,
        borderpad=4
    )
    fig_tech.update_layout(
        height=450,
        margin=dict(l=15, r=10, t=45, b=10),
        showlegend=False
    )
    st.plotly_chart(fig_tech, width="stretch", config=chart_config)

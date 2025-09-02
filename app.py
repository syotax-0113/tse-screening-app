# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="前日引け買いスクリーナー", layout="wide")
st.title("前日引け買い 翌日寄り売りスクリーナー（東証全銘柄対応）")

# 入力: CSVまたはテキストでティッカーコードを取得
uploaded_file = st.file_uploader("東証上場銘柄リストCSVをアップロード（Ticker列）", type=["csv"])
if uploaded_file is not None:
    tickers_df = pd.read_csv(uploaded_file)
    tickers = tickers_df["Ticker"].astype(str).tolist()
else:
    st.warning("CSVをアップロードしてください")
    st.stop()

# 条件設定
vol_ratio_threshold = st.number_input("出来高比率閾値", value=1.5, step=0.1)
price_change_threshold = st.number_input("値幅比率閾値", value=0.05, step=0.01)

st.write(f"対象銘柄数: {len(tickers)}")

# 分割取得設定
chunk_size = 50  # 一度に取得する銘柄数
candidates = []

# 進捗表示用
progress_bar = st.progress(0)
status_text = st.empty()

for i in range(0, len(tickers), chunk_size):
    chunk = tickers[i:i+chunk_size]
    for ticker in chunk:
        try:
            data = yf.download(ticker, period="10d", interval="1d", progress=False)
            if len(data) < 6:
                continue
            prev = data.iloc[-2]
            avg_vol = data['Volume'][-6:-1].mean()
            vol_ratio = prev['Volume'] / avg_vol
            price_change = abs(prev['High'] - prev['Close']) / prev['Close']
            if vol_ratio >= vol_ratio_threshold and price_change >= price_change_threshold:
                candidates.append({
                    "ticker": ticker,
                    "prev_close": prev['Close'],
                    "prev_high": prev['High'],
                    "vol_ratio": round(vol_ratio, 2),
                    "price_change_pct": round(price_change*100, 2)
                })
        except Exception as e:
            st.write(f"{ticker} 取得エラー: {e}")
            continue
    progress_bar.progress(min((i+chunk_size)/len(tickers),1))
    status_text.text(f"{min(i+chunk_size, len(tickers))}/{len(tickers)} 銘柄処理中...")
    time.sleep(0.5)  # 過負荷防止

# 結果表示
df = pd.DataFrame(candidates)
st.success(f"スクリーニング完了: {len(candidates)} 銘柄ヒット")
st.dataframe(df)

# CSVダウンロードリンク
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="結果をCSVでダウンロード",
    data=csv,
    file_name="candidates.csv",
    mime="text/csv"
)

import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="前日引け買いスクリーナー", layout="wide")
st.title("前日引け買い 翌日寄り売りスクリーナー（東証全銘柄対応）<br /><br />条件<br />Yahoo Finance から直近10日分の株価データを取得<br />
前日の出来高が直近5日平均より1.5倍以上か確認<br />
前日の高値から終値の変動率が5%以上か確認")

# ———————————————
# Google Drive にアップロードされた CSV を読み込む部分
drive_file_id = "1UVEFbA3nRy-gAD-weWsyaMYPmZUghY6U"
url = f"https://drive.google.com/uc?id={drive_file_id}"

@st.cache_data(ttl=600)
def load_tickers(url):
    df = pd.read_csv(url)
    return df

try:
    tickers_df = load_tickers(url)
except Exception as e:
    st.error(f"CSVの読み込みに失敗しました: {e}")
    st.stop()

# Ticker 列の確認と取得
if "Ticker" not in tickers_df.columns:
    st.error("CSVには「Ticker」という列が必要です。列名を確認してください。")
    st.stop()

tickers = tickers_df["Ticker"].astype(str).tolist()
st.write(f"読み込んだティッカー数: {len(tickers)}")

# ———————————————
# スクリーニング条件設定
vol_ratio_threshold = st.number_input("出来高比率閾値", value=1.5, step=0.1)
price_change_threshold = st.number_input("値幅比率閾値", value=0.05, step=0.01)

# 分割取得などの処理はここから下、既存のスクリーン処理を記述…
chunk_size = 50
candidates = []
progress_bar = st.progress(0)
status_text = st.empty()

for i in range(0, len(tickers), chunk_size):
    chunk = tickers[i:i + chunk_size]
    for ticker in chunk:
        try:
            data = yf.download(ticker, period="10d", interval="1d", progress=False)
            if len(data) < 6:
                continue
            prev = data.iloc[-2]
            avg_vol = data["Volume"][-6:-1].mean()
            vol_ratio = prev["Volume"] / avg_vol
            price_change = abs(prev["High"] - prev["Close"]) / prev["Close"]
            if vol_ratio >= vol_ratio_threshold and price_change >= price_change_threshold:
                candidates.append({
                    "ticker": ticker,
                    "prev_close": prev["Close"],
                    "prev_high": prev["High"],
                    "vol_ratio": round(vol_ratio, 2),
                    "price_change_pct": round(price_change * 100, 2)
                })
        except Exception as e:
            st.write(f"{ticker} 取得エラー: {e}")
    progress_bar.progress(min((i + chunk_size) / len(tickers), 1.0))
    status_text.text(f"{min(i + chunk_size, len(tickers))}/{len(tickers)} 銘柄処理中...")
    time.sleep(0.5)

df = pd.DataFrame(candidates)
st.success(f"スクリーニング完了: {len(candidates)} 銘柄ヒット")
st.dataframe(df)
csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("結果をCSVでダウンロード", data=csv, file_name="candidates.csv", mime="text/csv")

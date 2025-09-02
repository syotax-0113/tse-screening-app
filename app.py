import streamlit as st
import pandas as pd
import yfinance as yf

# Google Drive CSV URL
csv_url = "https://drive.google.com/uc?id=1UVEFbA3nRy-gAD-weWsyaMYPmZUghY6U&export=download"

st.title("東証銘柄スクリーニングアプリ")

# --- スクリーニング条件を表示 ---
st.markdown("""
### 📌 スクリーニング条件
- 対象: アップロード済みの銘柄リスト（CSVから取得）
- 直近 **5営業日** の株価データを取得
- 前日終値と翌日始値の **ギャップ率（%）** を計算
- 表示結果: 銘柄コード、前日終値、翌日始値、ギャップ率
""")

# データの読み込み
@st.cache_data
def load_data():
    df = pd.read_csv(csv_url)
    return df

tickers_df = load_data()
st.write("📂 銘柄リストを読み込みました:", tickers_df.shape)

# 実行ボタン
if st.button("スクリーニングを実行"):
    results = []
    for ticker in tickers_df["Ticker"].astype(str).tolist():
        try:
            data = yf.download(ticker + ".T", period="5d", interval="1d")
            if len(data) < 2:
                continue

            # 前日終値と当日始値のギャップを計算
            prev_close = data["Close"].iloc[-2]
            today_open = data["Open"].iloc[-1]
            gap = (today_open - prev_close) / prev_close * 100

            results.append({
                "Ticker": ticker,
                "前日終値": prev_close,
                "翌日始値": today_open,
                "ギャップ率(%)": round(gap, 2)
            })
        except Exception as e:
            st.write(f"{ticker} でエラー: {e}")

    if results:
        results_df = pd.DataFrame(results)
        st.dataframe(results_df)
        st.success("✅ スクリーニング完了")
    else:
        st.warning("⚠️ 結果がありません。")

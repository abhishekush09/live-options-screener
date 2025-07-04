import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import requests
import time

st.set_page_config(page_title="Live Options Screener", layout="wide")
st.title("🔍 Live Options Screener")

# 🔄 Auto-refresh slider
refresh_interval = st.slider("🔄 Auto-refresh every (seconds):", 15, 120, 60)
st_autorefresh(interval=refresh_interval * 1000, key="datarefresh")

# 👇 User selects the index
symbol = st.selectbox("Select Index:", ["NIFTY", "BANKNIFTY"])

# Function to fetch option chain from NSE
def fetch_option_chain():
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "*/*",
        "Referer": "https://www.nseindia.com/option-chain",
        "Connection": "keep-alive"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    response = session.get(url, headers=headers)

    if response.status_code != 200:
        st.error("❌ Failed to fetch data from NSE. Try again later.")
        return {"records": {"data": []}}  # safe fallback

    return response.json()

# Function to process and filter data
def process_option_chain(data):
    records = []
    for item in data.get('records', {}).get('data', []):
        strike = item.get('strikePrice')
        ce = item.get('CE')
        pe = item.get('PE')

        if ce:
            ce_signal = (ce.get('open') == ce.get('low')) and (ce.get('previousClose') < strike)
            records.append({
                'Strike': strike,
                'Type': 'CE',
                'Open': ce.get('open'),
                'High': ce.get('high'),
                'Low': ce.get('low'),
                'Prev Close': ce.get('previousClose'),
                'Signal': 'BUY CE' if ce_signal else ''
            })

        if pe:
            pe_signal = (pe.get('open') == pe.get('high')) and (pe.get('previousClose') > strike)
            records.append({
                'Strike': strike,
                'Type': 'PE',
                'Open': pe.get('open'),
                'High': pe.get('high'),
                'Low': pe.get('low'),
                'Prev Close': pe.get('previousClose'),
                'Signal': 'BUY PE' if pe_signal else ''
            })

    df = pd.DataFrame(records)

    if "Signal" in df.columns:
        return df[df["Signal"] != ""]
    else:
        return pd.DataFrame(columns=["Strike", "Type", "Open", "High", "Low", "Prev Close", "Signal"])

# Load and display data
data_load_state = st.text("Fetching option chain...")
data = fetch_option_chain()
df_filtered = process_option_chain(data)
data_load_state.text("Done!")

st.dataframe(df_filtered, use_container_width=True)

# Export filtered data to CSV
csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Signals as CSV", data=csv, file_name="option_signals.csv", mime="text/csv")

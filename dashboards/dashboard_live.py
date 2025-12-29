import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
import io
from minio import Minio
from datetime import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import os

# -------------------- CONFIG --------------------
REFRESH_INTERVAL = 30  # in seconds
MINIO_BUCKET = "stock-data-local"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# -------------------- UTILITY --------------------
# def get_latest_parquet_from_minio():
#     client = Minio(
#         MINIO_ENDPOINT,
#         access_key=MINIO_ACCESS_KEY,
#         secret_key=MINIO_SECRET_KEY,
#         secure=False
#     )

#     objects = client.list_objects(MINIO_BUCKET, recursive=True)
#     parquet_files = [obj for obj in objects if obj.object_name.endswith(".parquet")]
#     if not parquet_files:
#         raise FileNotFoundError("No Parquet files found in MinIO bucket.")

#     latest_file = max(parquet_files, key=lambda x: x.last_modified)
#     response = client.get_object(MINIO_BUCKET, latest_file.object_name)
#     return pd.read_parquet(io.BytesIO(response.read()))
def get_latest_parquet_from_minio(bucket_name='stock-data-local', prefix='streaming-output/', limit=10):
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
    parquet_files = sorted([obj.object_name for obj in objects if obj.object_name.endswith('.parquet')],
                           reverse=True)[:limit]

    dfs = []
    for file in parquet_files:
        response = minio_client.get_object(bucket_name, file)
        df = pd.read_parquet(io.BytesIO(response.read()))
        dfs.append(df)
        response.close()

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
# -------------------- STREAMLIT --------------------
st.set_page_config(page_title="📈 Live Stock Trends Dashboard", layout="wide")
st.title("📊 Real-Time Stock Ticker Dashboard")

# Autorefresh every N seconds
st_autorefresh(interval=REFRESH_INTERVAL * 1000, key="data-refresh")

# -------------------- LOAD DATA --------------------
try:
    df = get_latest_parquet_from_minio()
    st.success("Data loaded from MinIO ✅")
    st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()
# -------------------- DATA VALIDATION --------------------
# Ensure we have data
if df is None or df.empty:
    st.warning("No data available from MinIO. Make sure parquet files exist and contain rows.")
    st.stop()

# Ensure ticker column exists
if "ticker" not in df.columns:
    st.error(f"Required column 'ticker' not found in data. Available columns: {list(df.columns)}")
    st.stop()

# Pick a timestamp-like column and parse it
timestamp_candidates = ["timestamp", "ts", "time", "event_time"]
timestamp_col = next((c for c in timestamp_candidates if c in df.columns), None)

if timestamp_col is None:
    st.error(f"No timestamp column found. Expected one of {timestamp_candidates}. Available columns: {list(df.columns)}")
    st.stop()

try:
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
except Exception as e:
    st.error(f"Unable to parse '{timestamp_col}' as datetime: {e}")
    st.stop()

# Normalize to column name 'timestamp' for downstream code
if timestamp_col != "timestamp":
    df = df.rename(columns={timestamp_col: "timestamp"})

# -------------------- UI CONTROLS --------------------
ticker_options = df["ticker"].dropna().unique().tolist()
if not ticker_options:
    st.warning("No ticker values found in the data.")
    st.stop()

selected_ticker = st.selectbox("Select Ticker", ticker_options)

# Filter and ensure we have rows for the selected ticker
filtered_df = df[df["ticker"] == selected_ticker]
if filtered_df.empty:
    st.info(f"No rows found for ticker '{selected_ticker}'.")
    st.stop()

filtered_df = filtered_df.sort_values("timestamp")

# -------------------- METRICS --------------------
st.subheader(f"📌 Summary for {selected_ticker}")
col1, col2, col3 = st.columns(3)

col1.metric("Min Price", f"${filtered_df['price'].min():.2f}")
col2.metric("Max Price", f"${filtered_df['price'].max():.2f}")
col3.metric("Average Price", f"${filtered_df['price'].mean():.2f}")

# -------------------- PLOT --------------------
st.subheader("📈 Price Over Time")
fig = px.line(
    filtered_df,
    x="timestamp",
    y="price",
    title=f"Live Price Chart for {selected_ticker}",
    markers=True
)
fig.update_layout(xaxis_title="Timestamp", yaxis_title="Price", height=500)
st.plotly_chart(fig, use_container_width=True)

# -------------------- DATA TABLE --------------------
with st.expander("🧾 View Raw Data"):
    st.dataframe(filtered_df.tail(20), use_container_width=True)

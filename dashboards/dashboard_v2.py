import streamlit as st
import pandas as pd
import io
import boto3
import pyarrow
import plotly.graph_objects as go
import plotly.express as px

# --- MINIO CONFIG ---
MINIO_ENDPOINT = "localhost:9000"
MINIO_BUCKET = "stock-data-local"
MINIO_PREFIX = "streaming-output/"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
USE_SSL = False

# --- INIT MINIO ---
s3 = boto3.client(
    "s3",
    endpoint_url=f"http{'s' if USE_SSL else ''}://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

# --- FUNCTION TO GET PARQUET ---
def get_latest_parquet_from_minio():
    objects = s3.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=MINIO_PREFIX).get("Contents", [])
    parquet_files = [obj for obj in objects if obj["Key"].endswith(".parquet") and obj["Size"] > 0]
    
    if not parquet_files:
        raise FileNotFoundError("No parquet files found.")

    latest = max(parquet_files, key=lambda x: x["LastModified"])
    obj = s3.get_object(Bucket=MINIO_BUCKET, Key=latest["Key"])
    return pd.read_parquet(io.BytesIO(obj["Body"].read()))

# --- STREAMLIT DASH ---
st.set_page_config(page_title="📈 Real-time Stock Ticker", layout="wide")
st.title("📊 Live Stock Trends Dashboard")

try:
    df = get_latest_parquet_from_minio()

    # ✅ BASIC CLEANUP
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    tickers = df["ticker"].unique()

    selected_ticker = st.selectbox("Select Ticker", tickers)

    ticker_df = df[df["ticker"] == selected_ticker].sort_values("timestamp")

    # 🎯 CALCULATE STATS
    min_price = ticker_df["price"].min()
    max_price = ticker_df["price"].max()
    avg_price = ticker_df["price"].mean()

    st.markdown(f"### Stats for `{selected_ticker}`")
    col1, col2, col3 = st.columns(3)
    col1.metric("📉 Min", f"${min_price:.2f}")
    col2.metric("📈 Max", f"${max_price:.2f}")
    col3.metric("📊 Avg", f"${avg_price:.2f}")

    # 📊 PLOTLY CHART
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=ticker_df["timestamp"],
        y=ticker_df["price"],
        mode="lines+markers",
        name="Price",
        line=dict(color="royalblue")
    ))

    # Add horizontal lines
    fig.add_hline(y=min_price, line=dict(color="green", dash="dash"), annotation_text="Min", annotation_position="top left")
    fig.add_hline(y=max_price, line=dict(color="red", dash="dash"), annotation_text="Max", annotation_position="top right")
    fig.add_hline(y=avg_price, line=dict(color="orange", dash="dot"), annotation_text="Avg", annotation_position="bottom left")

    fig.update_layout(
        title=f"📈 Price Trend - {selected_ticker}",
        xaxis_title="Time",
        yaxis_title="Price",
        height=600,
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"💥 Something went wrong: {str(e)}")

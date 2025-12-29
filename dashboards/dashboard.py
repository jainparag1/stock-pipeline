import streamlit as st
import pandas as pd
import plotly.express as px
import boto3
import io
import os

st.set_page_config(layout="wide")
st.title("📈 Live Stock Price Trends (MinIO Powered)")

# 👇 MinIO / S3 settings
MINIO_ENDPOINT = "http://localhost:9000"
BUCKET_NAME = "stock-data-local"
PREFIX = "streaming-output/"  # Assuming all parquet files are here

# ✅ Create S3 client (for MinIO)
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
    region_name="us-east-1"
)

def get_latest_parquet_from_minio():
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX).get("Contents", [])
    
    # Grab only .parquet files
    parquet_files = [obj for obj in objects if obj["Key"].endswith(".parquet") and obj['Size'] > 0]
    if not parquet_files:
        raise FileNotFoundError("No valid parquet files found in MinIO.")

    latest_obj = max(parquet_files, key=lambda x: x["LastModified"])
    response = s3.get_object(Bucket=BUCKET_NAME, Key=latest_obj["Key"])

    buffer = io.BytesIO(response["Body"].read())
    return pd.read_parquet(buffer)


df = get_latest_parquet_from_minio()

if df.empty:
    st.warning("No data available in MinIO yet.")
else:
    # 🧮 Aggregation
    trend = df.groupby(['ticker', 'timestamp'])['price'].mean().reset_index()
    trend['timestamp'] = pd.to_datetime(trend['timestamp'])

    # 📊 Plot with Plotly
    fig = px.line(trend, x='timestamp', y='price', color='ticker',
                  title='Real-Time Stock Price Trends', markers=True)
    fig.update_layout(xaxis_title="Time", yaxis_title="Price", legend_title="Ticker")
    st.plotly_chart(fig, use_container_width=True)
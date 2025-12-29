# stream_processor_partitioned.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, year, month, dayofmonth, hour
from pyspark.sql.types import StructType, StringType, DoubleType, IntegerType, LongType
import os

# ---------- Config (customize) ----------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_PATH = "s3a://stock-data-local/streaming-output"   # target prefix
CHECKPOINT_PATH = "s3a://stock-data-local/checkpoints/stock-stream/"  # checkpoint prefix

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "stock-ticks")

# ---------- Spark session ----------
spark = SparkSession.builder \
    .appName("KafkaSparkStockStreamPartitioned") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.sql.parquet.mergeSchema", "false") \
    .getOrCreate()

# ---------- Schema ----------
schema = StructType() \
    .add("ticker", StringType()) \
    .add("price", DoubleType()) \
    .add("volume", IntegerType()) \
    .add("timestamp", DoubleType())  # epoch seconds

# ---------- Read stream from Kafka ----------
raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# ---------- Parse JSON payload ----------
parsed = raw.selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json(col("json_str"), schema).alias("data")) \
    .select("data.*")

# ---------- Convert timestamp and add partition columns ----------
# assuming timestamp is epoch seconds (float/double). If ISO string, use to_timestamp directly
df = parsed.withColumn("ts", to_timestamp((col("timestamp")).cast("double"))) \
    .withColumn("year", year(col("ts"))) \
    .withColumn("month", month(col("ts"))) \
    .withColumn("day", dayofmonth(col("ts"))) \
    .withColumn("hour", hour(col("ts")))

# optional: reorder or cast types
df = df.select("ticker", "price", "volume", "ts", "year", "month", "day", "hour")

# ---------- Write stream to S3A (MinIO) partitioned by year/month/day/hour ----------
query = df.writeStream \
    .format("parquet") \
    .option("path", MINIO_BUCKET_PATH) \
    .option("checkpointLocation", CHECKPOINT_PATH) \
    .partitionBy("year", "month", "day", "hour") \
    .outputMode("append") \
    .trigger(processingTime="30 seconds") \
    .start()

query.awaitTermination()

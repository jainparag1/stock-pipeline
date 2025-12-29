from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, DoubleType, LongType, IntegerType

# Define schema
schema = StructType() \
    .add("ticker", StringType()) \
    .add("price", DoubleType()) \
    .add("volume", IntegerType()) \
    .add("timestamp", DoubleType())

# Create SparkSession
spark = SparkSession.builder \
    .appName("KafkaSparkMinioStream") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# Read from Kafka
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "stock-ticks") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# Decode the value from Kafka
df_parsed = df_raw.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Output to console
# query = df_parsed.writeStream \
#     .outputMode("append") \
#     .format("console") \
#     .option("truncate", "false") \
#     .start()
query = df_parsed \
    .writeStream \
    .format("parquet") \
    .option("fs.s3a.endpoint", "http://localhost:9000") \
    .option("fs.s3a.access.key", "minioadmin") \
    .option("fs.s3a.secret.key", "minioadmin") \
    .option("fs.s3a.path.style.access", "true") \
    .option("fs.s3a.connection.ssl.enabled", "false") \
    .option("path", "s3a://stock-data-local/streaming-output/") \
    .option("checkpointLocation", "s3a://stock-data-local/checkpoints/") \
    .outputMode("append") \
    .start()
    
query.awaitTermination()

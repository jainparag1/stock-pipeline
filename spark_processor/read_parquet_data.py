from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import time

# Create Spark session
spark = SparkSession.builder \
    .appName("Read Parquet Data") \
    .getOrCreate()

# Path to your parquet output
parquet_path = "/mnt/d/Parag/Learning/projects/stock-pipeline/output"

# Read the data
df = spark.read.parquet(parquet_path)

# Show some rows
# df.show(truncate=False)


while True:
    df = spark.read.parquet(parquet_path)
    df.orderBy("timestamp", ascending=False).show(5, truncate=False)
    time.sleep(5)
# df_filtered = df.filter(col("timestamp") >= "2025-08-03T17:00:00")
# df_filtered.show()
# Optional: Schema peek
df.printSchema()
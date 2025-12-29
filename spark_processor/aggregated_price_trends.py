from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, max, min, count

# Initialize Spark session
spark = SparkSession.builder \
    .appName("Aggregated Price Trends........") \
    .getOrCreate()

# Path to your parquet files
parquet_path = "/mnt/d/Parag/Learning/projects/stock-pipeline/output"

# Load the data
df = spark.read.parquet(parquet_path)

# Group by ticker and compute aggregates
agg_df = df.groupBy("ticker").agg(
    count("*").alias("total_records"),
    avg("price").alias("avg_price"),
    min("price").alias("min_price"),
    max("price").alias("max_price")
)

# Sort by average price (optional)
agg_df = agg_df.orderBy("avg_price", ascending=False)

# Display results
agg_df.show(truncate=False)

# Optional: Save to a new file
agg_df.write.mode("overwrite").parquet("/mnt/d/Parag/Learning/projects/stock-pipeline/aggregates")

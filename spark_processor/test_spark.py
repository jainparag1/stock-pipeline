# test_spark.py
from pyspark.sql import SparkSession

spark = SparkSession.builder.master("local[*]").getOrCreate()
print(spark.version)
spark.stop()
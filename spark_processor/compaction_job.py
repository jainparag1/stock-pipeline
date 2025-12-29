"""
compaction_job.py

Usage:
  spark-submit --master local[*] ... compaction_job.py \
    --base-path s3a://stock-data/streaming-output \
    --partitions "year=2025,month=08,day=30" \
    --num-files 1

Notes:
- This uses Spark's dynamic partition overwrite mode to replace only the partitions present in the dataframe.
- For safety, it reads partitions, repartitions into num_files, then writes back with overwrite + dynamic mode.
"""
import argparse
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# ---------- Config (customize) ----------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_PATH = "s3a://stock-data-local/streaming-output"   # target prefix

def create_spark(app_name="compaction-job"):
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
        .getOrCreate()

def parse_partitions_string(p_str):
    # p_str example: "year=2025,month=08,day=03" OR multiple partitions separated by ';'
    partitions = []
    if not p_str:
        return partitions
    groups = p_str.split(";")
    for g in groups:
        kvs = dict([kv.split("=",1) for kv in g.split(",")])
        partitions.append(kvs)
    return partitions

def partition_path(base_path, part_dict):
    parts = [f"{k}={v}" for k, v in part_dict.items()]
    return base_path.rstrip("/") + "/" + "/".join(parts)

def compact_one_partition_old(spark, base_path, part_dict, num_files):
    ppath = partition_path(base_path, part_dict)
    print(f"[compaction] reading partition: {ppath}")
    try:
        df = spark.read.parquet(ppath)
    except Exception as e:
        print(f"[compaction] could not read {ppath}: {e}")
        return False

    if df.rdd.isEmpty():
        print(f"[compaction] partition empty: {ppath}")
        return True

    # NOTE: Ensure partition columns exist in df if you will use partitionBy when writing
    # If parquet files already contain the partition columns (year,month,day,hour), good.
    print(f"[compaction] rows={df.count()}, repartitioning -> {num_files} files")
    compacted = df.repartition(num_files)

    # Write back using dynamic overwrite (only partitions present in `compacted` will be replaced)
    print(f"[compaction] writing back to base path: {base_path} (dynamic overwrite)")
    compacted.write \
        .mode("overwrite") \
        .option("partitionOverwriteMode", "dynamic") \
        .partitionBy(*list(part_dict.keys())) \
        .parquet(base_path)

    print(f"[compaction] done for {ppath}")
    return True
from pyspark.sql import functions as F

def compact_one_partition(spark, base_path, part_dict, num_files):
    ppath = partition_path(base_path, part_dict)
    print(f"[compaction] Reading partition from: {ppath}")

    try:
        df = spark.read.parquet(ppath)
    except Exception as e:
        print(f"[compaction] Could not read {ppath}: {e}")
        return False

    # Add back missing partition columns if absent
    for col_name, col_val in part_dict.items():
        if col_name not in df.columns:
            df = df.withColumn(col_name, F.lit(int(col_val)))

    row_count = df.count()
    print(f"[compaction] rows={row_count}, repartitioning into {num_files} files")
    if row_count == 0:
        print(f"[compaction] Partition empty: {partition_path}")
        return True

    compacted = df.repartition(num_files)

    print(f"[compaction] Writing back to base path with dynamic overwrite: {base_path}")
    compacted.write \
        .mode("overwrite") \
        .option("partitionOverwriteMode", "dynamic") \
        .partitionBy(*part_dict.keys()) \
        .parquet(base_path)

    print(f"[compaction] Completed compaction for {partition_path}")
    return True

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-path", required=True, help="S3A base path where data is stored (e.g. s3a://stock-data/streaming-output)")
    p.add_argument("--partitions", required=True,
                   help='Partitions list. Example single partition: "year=2025,month=08,day=30". For multiple, separate with ";"')
    p.add_argument("--num-files", type=int, default=1, help="Target number of files per partition")
    args = p.parse_args()
    # stock-data-local/streaming-output/year=2025/month=8/day=9/hour=23
    spark = create_spark("parquet-compaction-job")
    partitions = parse_partitions_string(args.partitions)
    if not partitions:
        print("No partitions provided - exiting.")
        return

    for part in partitions:
        ok = compact_one_partition(spark, args.base_path, part, args.num_files)
        if not ok:
            print(f"[compaction] failed for {part}")

    spark.stop()

if __name__ == "__main__":
    main()

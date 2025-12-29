#!/usr/bin/env bash
set -eu
# wrapper to run the compaction job
BASE_PATH=${1:-"s3a://stock-data-local/streaming-output"}
PARTITIONS=${2:-"year=2025,month=8,day=10"}   # example: "year=2025,month=08,day=03"
NUM_FILES=${3:-1}
JARS_DIR="/mnt/d/Parag/Learning/projects/stock-pipeline/jars"

JARS=$(echo ${JARS_DIR}/*.jar | tr ' ' ',')
echo "[run_compaction] JARS=$JARS"
spark-submit \
  --master local[*] \
  --class org.apache.spark.deploy.SparkSubmit \
  --conf "spark.driver.extraClassPath=$(echo /mnt/d/Parag/Learning/projects/stock-pipeline/jars/*.jar | tr ' ' ':')" \
  --conf "spark.executor.extraClassPath=$(echo /mnt/d/Parag/Learning/projects/stock-pipeline/jars/*.jar | tr ' ' ':')" \
  --conf "spark.hadoop.fs.s3a.endpoint=http://localhost:9000" \
  --conf "spark.hadoop.fs.s3a.path.style.access=true" \
  --conf "spark.hadoop.fs.s3a.connection.ssl.enabled=false" \
  --conf "spark.hadoop.fs.defaultFS=s3a://stock-data-local" \
  --jars "${JARS}" \
  /mnt/d/Parag/Learning/projects/stock-pipeline/spark_processor/compaction_job.py \
  --base-path "${BASE_PATH}" \
  --partitions "${PARTITIONS}" \
  --num-files "${NUM_FILES}"
#!/bin/bash
export SPARK_DIST_CLASSPATH=$(echo /mnt/d/Parag/Learning/projects/stock-pipeline/jars/*.jar | tr ' ' ':')

spark-submit \
  --class org.apache.spark.deploy.SparkSubmit \
  --conf "spark.driver.extraClassPath=$(echo /mnt/d/Parag/Learning/projects/stock-pipeline/jars/*.jar | tr ' ' ':')" \
  --conf "spark.executor.extraClassPath=$(echo /mnt/d/Parag/Learning/projects/stock-pipeline/jars/*.jar | tr ' ' ':')" \
  --jars $(echo /mnt/d/Parag/Learning/projects/stock-pipeline/jars/*.jar | tr ' ' ',') \
  /mnt/d/Parag/Learning/projects/stock-pipeline/spark_processor/stream_processor_partitioned.py

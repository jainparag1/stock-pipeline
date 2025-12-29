from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 8, 10),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "spark_compaction_job",
    default_args=default_args,
    schedule_interval="*/10 * * * *",  # every 10 minutes
    catchup=False,
) as dag:

    compact_task = BashOperator(
        task_id="compact_parquet_partitions",
        bash_command="""
        "/mnt/d/Parag/Learning/projects/stock-pipeline/spark_processor/bin/run_compaction.sh"
        """
    )

    compact_task

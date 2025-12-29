from airflow import DAG
import logging
from airflow.exceptions import AirflowException
try:
    # Airflow 2.x
    from airflow.operators.python import PythonOperator
except Exception:
    # fallback for some environments
    from airflow.operators.python_operator import PythonOperator
import subprocess
from datetime import datetime, timedelta
import json
import os
import re
from airflow.models import Variable

# DAG definition
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="compaction_job_dag",
    default_args=default_args,
    description="Run Spark compaction job and store in MinIO",
    schedule_interval="*/30 * * * *",  # every 2 minutes
    start_date=datetime(2025, 8, 30), # adjust as needed
    catchup=False,
    tags=["spark", "compaction", "minio"],
) as dag:

    def _run_compaction_script(**context):
        script_path = "/mnt/d/Parag/Learning/projects/stock-pipeline/spark_processor/bin/run_compaction.sh"
        # derive partitions from execution_date (fallback to now)
        exec_date = context.get("execution_date")
        if exec_date is None:
            exec_date = datetime.utcnow()

        # zero-pad month/day to match common partition naming (e.g. month=08)
        partitions = f"year={exec_date.year},month={exec_date.month:01d},day={exec_date.day:02d}"
        base_path = "s3a://stock-data-local/streaming-output"
        num_files = 1

        logging.info(f"Running compaction script: {script_path} base_path={base_path} partitions={partitions} num_files={num_files}")
        try:
            subprocess.run(["/bin/bash", script_path, base_path, partitions, str(num_files)], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Compaction script failed with exit code {e.returncode}")
            raise AirflowException(f"Compaction script failed: {e}")

    run_compaction = PythonOperator(
        task_id="run_compaction",
        python_callable=_run_compaction_script,
    )


    def _snapshot_before(**context):
        # call the minio snapshot helper and write to a before file
        script = "/mnt/d/Parag/Learning/projects/stock-pipeline/infra/minio_compaction_check.py"
        out = "/tmp/minio_snapshot_before.json"
        cmd = ["python3", script, "snapshot", "--endpoint", "http://localhost:9000", "--access-key", "minioadmin", "--secret-key", "minioadmin", "--bucket", "stock-data-local", "--prefix", "streaming-output", "--out", out]
        logging.info("Running snapshot before compaction: %s", cmd)
        subprocess.run(cmd, check=True)


    def _snapshot_after(**context):
        script = "/mnt/d/Parag/Learning/projects/stock-pipeline/infra/minio_compaction_check.py"
        out = "/tmp/minio_snapshot_after.json"
        cmd = ["python3", script, "snapshot", "--endpoint", "http://localhost:9000", "--access-key", "minioadmin", "--secret-key", "minioadmin", "--bucket", "stock-data-local", "--prefix", "streaming-output", "--out", out]
        logging.info("Running snapshot after compaction: %s", cmd)
        subprocess.run(cmd, check=True)


    def _assert_compaction(**context):
        before = "/tmp/minio_snapshot_before.json"
        after = "/tmp/minio_snapshot_after.json"
        if not os.path.exists(before) or not os.path.exists(after):
            raise AirflowException("Missing snapshot files for compaction assertion")
        with open(before) as f:
            b = json.load(f)
        with open(after) as f:
            a = json.load(f)
        files_before = b.get('files', [])
        files_after = a.get('files', [])
        count_before = len(files_before)
        count_after = len(files_after)

        # Configurable behavior via Airflow Variables (set in UI or env):
        # compaction_min_reduction_pct: minimum percent reduction required (default 0)
        # compaction_per_partition: if 'true', check reduction per partition (default false)
        try:
            min_reduction_pct = float(Variable.get('compaction_min_reduction_pct', default_var='0'))
        except Exception:
            min_reduction_pct = 0.0
        per_partition = str(Variable.get('compaction_per_partition', default_var='false')).lower() == 'true'

        logging.info(f"Compaction check: before={count_before} after={count_after} min_pct={min_reduction_pct} per_partition={per_partition}")

        def extract_partition_label(key: str) -> str:
            # build a short partition label like year=.../month=.../day=...
            parts = []
            for seg in key.split('/'):
                if '=' in seg:
                    k, v = seg.split('=', 1)
                    if k in ('year', 'month', 'day'):
                        parts.append(f"{k}={v}")
            return '/'.join(parts) if parts else 'ungrouped'

        if per_partition:
            # build counts per partition from the before/after snapshots
            before_map = {}
            for f in files_before:
                label = extract_partition_label(f['Key'])
                before_map[label] = before_map.get(label, 0) + 1
            after_map = {}
            for f in files_after:
                label = extract_partition_label(f['Key'])
                after_map[label] = after_map.get(label, 0) + 1

            # check each partition present in before
            failed = []
            for label, bcount in before_map.items():
                acount = after_map.get(label, 0)
                reduction_pct = (bcount - acount) / bcount * 100 if bcount > 0 else 0.0
                logging.info(f"Partition {label}: before={bcount} after={acount} reduction_pct={reduction_pct:.1f}%")
                if reduction_pct < min_reduction_pct:
                    failed.append((label, bcount, acount, reduction_pct))

            if failed:
                msgs = [f"{lab}: before={bb} after={aa} reduction={rp:.1f}%" for lab, bb, aa, rp in failed]
                raise AirflowException("Compaction per-partition checks failed: " + "; ".join(msgs))
        else:
            # overall check
            if count_before == 0:
                logging.info("No files before compaction; nothing to assert.")
                return
            reduction_pct = (count_before - count_after) / count_before * 100
            if reduction_pct < min_reduction_pct:
                raise AirflowException(f"Compaction reduction {reduction_pct:.1f}% is below required {min_reduction_pct}% (before={count_before} after={count_after})")


    snapshot_before = PythonOperator(
        task_id="snapshot_before",
        python_callable=_snapshot_before,
    )

    snapshot_after = PythonOperator(
        task_id="snapshot_after",
        python_callable=_snapshot_after,
    )

    assert_compaction = PythonOperator(
        task_id="assert_compaction",
        python_callable=_assert_compaction,
    )

    snapshot_before >> run_compaction >> snapshot_after >> assert_compaction

    run_compaction

MinIO compaction verification

This folder contains a small helper and a wrapper to verify that your Spark compaction job actually reduces the number of parquet files in MinIO.

Files
- minio_compaction_check.py  - CLI to snapshot/list/diff parquet files in a bucket/prefix (uses boto3)
- run_compaction_and_check.sh - Wrapper script that: snapshot before -> run compaction script -> snapshot after -> assert reduction

Quick usage (WSL / bash)
1. Snapshot only (ad-hoc):

```bash
python3 infra/minio_compaction_check.py summary \
  --endpoint http://localhost:9000 --access-key minioadmin --secret-key minioadmin \
  --bucket stock-data-local --prefix streaming-output
```

2. Manual snapshot to file:

```bash
python3 infra/minio_compaction_check.py snapshot \
  --endpoint http://localhost:9000 --access-key minioadmin --secret-key minioadmin \
  --bucket stock-data-local --prefix streaming-output --out /tmp/minio_before.json
```

3. Run the wrapper (dry-run first):

```bash
bash infra/run_compaction_and_check.sh --dry-run \
  --compaction-script /mnt/d/Parag/Learning/projects/stock-pipeline/spark_processor/bin/run_compaction.sh \
  --base-path s3a://stock-data-local/streaming-output \
  --partitions "year=2025,month=8,day=30" \
  --num-files 1
```

4. Run for real (the wrapper will exit non-zero if file-count did not reduce):

```bash
bash infra/run_compaction_and_check.sh \
  --compaction-script /mnt/d/Parag/Learning/projects/stock-pipeline/spark_processor/bin/run_compaction.sh \
  --base-path s3a://stock-data-local/streaming-output \
  --partitions "year=2025,month=8,day=30" \
  --num-files 1
```

Airflow integration
- You can call the wrapper from an Airflow `BashOperator` instead of directly invoking the compaction script. Example:

  BashOperator(
    task_id='wrap_compaction',
    bash_command='bash /path/to/repo/infra/run_compaction_and_check.sh --compaction-script /path/to/run_compaction.sh --base-path s3a://... --partitions "year={{ ds.split("-")[0] }},month={{ macros.ds_format(ds, "%Y-%m-%d", "%m") }},day={{ macros.ds_format(ds, "%Y-%m-%d", "%d") }}" --num-files 1'
  )

Security
- Avoid embedding credentials in DAGs or shell scripts. Use Airflow Connections or environment variables. The wrapper supports passing endpoint/access-key/secret-key flags; prefer reading them from secure sources.

Notes
- The wrapper checks only the total file count by default. For stronger guarantees use the Airflow-enhanced DAG changes (per-partition checks) already in the repo.
- The helper requires `boto3` and `botocore` installed in the environment where it's run.

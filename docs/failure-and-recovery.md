🔥 Failure Scenarios & Recovery Guide

Stock Market Streaming Platform

1. Kafka Producer Failure
Scenario

The stock data simulator crashes or stops sending events.

Impact

No new events published

Downstream systems remain idle

No data loss

Detection

Kafka topic lag stops increasing

Spark streaming shows zero input rows/sec

Recovery

Restart producer

Kafka retains previous data

Spark resumes consumption automatically

Why This Is Safe

Kafka decouples ingestion from processing, providing natural buffering.

2. Kafka Broker Restart / Offset Issues
Scenario

Kafka broker restarts or topic offsets reset during development.

Impact

Potential offset mismatch

Spark streaming job may fail

Detection

Spark logs show offset inconsistency

Streaming query terminates

Recovery

Restart Spark job

Use failOnDataLoss=false (development only)

In production, enable Kafka retention safeguards

Trade-off

Prefers data availability during development over strict guarantees.

3. Spark Streaming Job Crash
Scenario

Spark process crashes due to OOM, dependency issue, or node failure.

Impact

Streaming pauses temporarily

No data corruption

Detection

Spark UI shows terminated query

No new files written

Recovery

Restart streaming job

Spark resumes from last checkpoint

Exactly-once semantics preserved

Key Mechanism

Spark checkpoints store offsets and state.

4. MinIO / Object Storage Outage
Scenario

MinIO service becomes unavailable.

Impact

Streaming job fails on write

Kafka continues accumulating data

Detection

Spark write failures

MinIO health checks fail

Recovery

Restart MinIO

Restart Spark streaming job

Backlog processed automatically

Why This Works

Storage is downstream of Kafka — ingestion continues safely.

5. Small File Explosion
Scenario

High-frequency streaming produces thousands of tiny Parquet files.

Impact

Query performance degradation

Increased metadata overhead

Detection

Excessive file count per partition

Slower DuckDB/dbt queries

Recovery

Trigger compaction job

Overwrite only affected partitions

Restore optimal file sizes

6. Compaction Job Failure
Scenario

Compaction Spark job fails mid-run.

Impact

Partition remains unoptimized

No data loss

Detection

Airflow DAG failure

Partial overwrite prevented by Spark semantics

Recovery

Rerun compaction DAG

Idempotent by partition

7. Airflow Scheduler Down
Scenario

Airflow scheduler crashes.

Impact

No scheduled compactions

Streaming unaffected

Detection

DAGs not triggering

Airflow UI unavailable

Recovery

Restart scheduler

Manual backfill if needed

8. dbt Model Failure
Scenario

Schema mismatch or missing partition causes dbt failure.

Impact

Analytics models not refreshed

Raw data remains intact

Detection

dbt run errors

CI or logs show failing model

Recovery

Fix model logic

Re-run dbt

No impact on upstream systems

9. Dashboard Failure
Scenario

Streamlit dashboard crashes or loses connectivity.

Impact

Visualization unavailable

Data pipeline continues running

Detection

UI inaccessible

Recovery

Restart dashboard

Stateless design enables fast recovery

🎯 Design Philosophy

This system is designed so that:

Failures are isolated

Recovery is predictable

No single failure causes data loss

Data pipelines should bend, not break.

📌 Key Takeaway

Most failures are operational, not architectural.
This platform is designed to fail safely and recover cleanly.
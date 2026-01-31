# 📈 Stock Market Streaming Platform

This repository contains a production-style, end-to-end **real-time stock market streaming and analytics platform** built to demonstrate modern data engineering, streaming systems, and lakehouse architecture using open-source tools.

The platform simulates high-frequency stock market ticks, ingests them through **Kafka**, processes them using **Spark Structured Streaming**, stores them in an **S3-compatible lakehouse (MinIO)**, compacts data using **Spark batch jobs**, orchestrated by **Airflow**, models analytics using **dbt with DuckDB**, and visualizes insights via a **Streamlit** dashboard.

This project is intentionally designed to reflect **real-world system design trade-offs**, operational challenges, and recovery patterns rather than toy examples or tutorial shortcuts. It is aimed at showcasing strong hands-on expertise in **streaming systems, distributed data processing, orchestration, and analytics engineering**, with a clear focus on senior engineer, tech lead, and CTO-level expectations.

At a high level, the architecture follows this flow:

**Decoupled Streaming Ingestion** → Kafka buffers events, decoupling producers from consumers. -> **Stateful Stream Processing** → Spark Structured Streaming with checkpointing ensures exactly-once semantics and safe restarts. -> **Lakehouse Storage** → Partitioned Parquet on MinIO enables cost-efficient, queryable long-term storage. -> **Intelligent Compaction** → Automated Spark batch jobs eliminate the small-file problem without manual intervention. -> **Scheduled Orchestration** → Airflow provides observability, retries, and failure recovery for all batch workloads. -> 
**Analytics Layer** → dbt models and DuckDB deliver fast SQL-based insights without external dependencies. -> **User Dashboards** → Stateless Streamlit app visualizes trends, volumes, and anomalies in real time.

The repository is structured as follows:

- `data_simulator/` contains Kafka producers that generate synthetic stock tick data.
- `spark_processor/` contains Spark Structured Streaming jobs and batch compaction logic, including the `run_compaction.sh` entrypoint.
- `jars/` contains explicitly managed Spark, Hadoop, and Kafka connector dependencies.
- `output/` stores raw streaming parquet data.
- `aggregates/` stores aggregated or transformed parquet outputs.
- `checkpoint/` contains Spark Structured Streaming checkpoints for exactly-once processing guarantees.
- `airflow/` contains DAGs used to orchestrate Spark compaction jobs on a schedule.
- `dbt_models/` contains the dbt project configured with DuckDB for fast local analytics on parquet data.
- `dashboards/` contains Streamlit applications for real-time and analytical visualization.
- `infra/` contains infrastructure setup (Docker, MinIO, Airflow).
- `docs/` contains architecture, design decisions, and failure-recovery documentation.
- `artifacts/` contains screenshots, diagrams, and demo assets.
- `logs/` stores runtime logs.
- `venv/` contains the Python virtual environment.
- `spark-4.0.0-bin-hadoop3.tgz` is the Spark distribution used by the project.

The platform demonstrates several key engineering concepts: decoupled ingestion using Kafka, stateful and fault-tolerant stream processing with Spark Structured Streaming, lakehouse-style storage on object storage, mitigation of the small-file problem via compaction, workflow orchestration with Airflow, analytics modeling using dbt, and lightweight BI using Streamlit.

Failure handling and recovery are first-class design considerations. Spark streaming jobs rely on checkpoints for restartability, compaction jobs are idempotent and partition-aware, Airflow provides retries and observability, and analytics layers are fully decoupled from ingestion so downstream failures do not impact upstream systems. Detailed recovery scenarios are documented under `docs/`.

To run the platform locally, start the infrastructure (Kafka, MinIO, Airflow) using Docker, launch the data simulator to emit stock ticks, run the Spark streaming job to ingest and persist data, allow Airflow to trigger compaction jobs, execute dbt models to build analytical tables, and finally launch the Streamlit dashboard to visualize trends such as price movements, volume spikes, and aggregated metrics.

This project is designed for extensibility. Planned enhancements include schema registry integration, Delta Lake or Iceberg support, stronger end-to-end exactly-once guarantees, cloud-native deployment on AWS or GCP, and CI/CD pipelines for Spark, Airflow, and dbt workflows.

Please refer the documents under `docs/` section for **architecture, executive summary** and **running this project locally...!**

Author: **Parag Jain**  
Director Software Engineering | Streaming & Data Platforms | Aspiring CTO  
GitHub: https://github.com/jainparag1  
Linkedin: https://www.linkedin.com/in/parag-jain-0395011

This repository is intended for recruiters, hiring managers, startup founders, and senior engineers who want to evaluate real-world streaming and lakehouse system design skills beyond tutorials and boilerplate demos.

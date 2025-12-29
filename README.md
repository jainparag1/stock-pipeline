📈 Stock Market Streaming Platform

Real-time Stock Data Pipeline | Kafka • Spark • MinIO • Airflow • dbt • DuckDB

A production-style, end-to-end real-time stock market data platform showcasing streaming, lakehouse architecture, and analytics engineering — built with scalability, observability, and orchestration in mind.

🚀 Why This Project?

This project was built to demonstrate how modern data platforms actually work in the real world, not just in tutorials.

It focuses on:

⚡ Real-time streaming with Spark Structured Streaming

🧱 Lakehouse-style storage using Parquet on MinIO (S3-compatible)

🔁 Data compaction & optimization (often ignored, always critical)

🛠️ Workflow orchestration with Airflow

📊 Analytics & modeling using dbt + DuckDB

📺 Live visualization via Streamlit

This is the kind of system you’d expect in:

Fintechs

Trading platforms

Data-driven startups

Modern cloud-native data teams

🧠 High-Level Architecture
┌──────────────┐
│ Data Simulator│
│ (Stock Ticks) │
└──────┬───────┘
       ▼
┌──────────────┐
│    Kafka     │
│ (Raw Events) │
└──────┬───────┘
       ▼
┌──────────────────────────┐
│ Spark Structured Streaming│
│ - Parsing & validation    │
│ - Event-time processing   │
│ - Parquet writes          │
└──────┬───────────────────┘
       ▼
┌──────────────────────────┐
│ MinIO (S3-compatible)     │
│ - Raw streaming parquet   │
│ - Partitioned by date     │
└──────┬───────────────────┘
       ▼
┌──────────────────────────┐
│ Spark Compaction Job      │
│ - File consolidation      │
│ - Optimized partitions    │
└──────┬───────────────────┘
       ▼
┌──────────────────────────┐
│ Analytics Layer           │
│ - dbt models              │
│ - DuckDB engine           │
└──────┬───────────────────┘
       ▼
┌──────────────────────────┐
│ Streamlit Dashboard       │
│ - Live price trends       │
│ - Min / Max / Avg         │
└──────────────────────────┘

📂 Project Structure (Aligned to Production Thinking)
stock-pipeline/
│
├── data_simulator/        # Kafka producer simulating stock ticks
│
├── spark_processor/       # Core Spark logic
│   ├── stream_processor.py   # Structured Streaming consumer
│   ├── compaction_job.py     # Parquet compaction job
│   └── run_compaction.sh     # Spark-submit wrapper
│
├── jars/                  # Explicit Spark / Hadoop / Kafka dependencies
│
├── output/                # Raw streaming parquet output
├── aggregates/            # Aggregated parquet datasets
├── checkpoint/            # Spark streaming checkpoints
│
├── dashboards/            # Streamlit live dashboard
│   └── dashboard_live.py
│
├── airflow/               # Airflow DAGs
│   └── dags/
│
├── dbt_models/            # dbt + DuckDB analytics layer
│   ├── models/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── dev.duckdb
│
├── infra/                 # MinIO / Docker / infra setup
├── artifacts/             # Screenshots, diagrams, demo assets
├── docs/                  # Architecture & design notes
├── logs/                  # Runtime logs
├── venv/                  # Python virtual environment
│
├── README.md
└── spark-4.0.0-bin-hadoop3.tgz

⚙️ Key Features
⚡ Real-Time Streaming

Kafka-based stock tick ingestion

Spark Structured Streaming with event-time processing

Fault tolerance via checkpoints

🧱 Lakehouse Storage

Parquet-based storage on MinIO (S3-compatible)

Partitioned by year / month / day / hour

Optimized for downstream analytics

🔁 Compaction & Optimization

Periodic Spark batch job

Reduces small-file problem

Orchestrated via Airflow (cron-style DAG)

📊 Analytics with dbt + DuckDB

SQL-first transformations

Fast local analytics without external warehouses

Easy transition to Trino / Athena / Snowflake later

📺 Live Dashboard

Streamlit-based UI

Live price trends per ticker

Min / Max / Average overlays

Auto-refresh for near real-time insights

🛠️ Tech Stack
Layer	Technology
Ingestion	Kafka
Stream Processing	Apache Spark
Storage	MinIO (S3-compatible)
Orchestration	Apache Airflow
Analytics	dbt + DuckDB
Visualization	Streamlit
Language	Python, SQL
Format	Parquet
🎯 What This Project Demonstrates

End-to-end ownership mindset

Production-aware Spark & Hadoop internals

Real-world data engineering trade-offs

Ability to design systems, not just write code

In short: how a Tech Lead thinks about data platforms.

🧭 Roadmap

 Trino / Athena-style query engine

 Schema evolution handling

 Metrics & data quality checks

 Cloud deployment (AWS / GCP)

 CI/CD for data pipelines

👋 About Me

Built by Parag Jain
Senior Software Engineer | Data & Streaming Enthusiast
Aiming for CTO / Tech Lead roles in high-impact startups
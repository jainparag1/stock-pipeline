🏗️ System Architecture – Stock Market Streaming Platform
1. Overview

This document describes the end-to-end architecture of the Stock Market Streaming Platform, a real-time data pipeline designed to ingest, process, store, optimize, and analyze stock market events at scale.

The system follows modern lakehouse principles and separates concerns across:

• Ingestion
• Stream processing
• Storage
• Optimization
• Analytics
• Visualization
• Orchestration

The architecture is intentionally modular to allow future migration to managed cloud services without redesign.

2. Design Principles

The platform was designed around the following principles:

🔹 Real-Time First

• Streaming ingestion using Kafka  
• Low-latency processing via Spark Structured Streaming  
• Event-time aware processing  

🔹 Storage as the Source of Truth

• Immutable Parquet files
• Append-only streaming writes
• Optimized for reprocessing and backfills

🔹 Separation of Compute & Storage

• Stateless Spark jobs
• Object storage (MinIO) as durable layer
• Independent scaling of components

🔹 Production Awareness

• Checkpointing & fault tolerance
• Compaction to solve small-file problem
• Orchestration via Airflow
• Analytics isolated from ingestion

3. High-Level Architecture Diagram
┌──────────────────┐
│ Data Simulator   │
│ (Stock Generator)│
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Kafka Topics     │
│ stock-ticks      │
└────────┬─────────┘
         ▼
┌────────────────────────────────┐
│ Spark Structured Streaming     │
│ - Schema enforcement           │
│ - Event-time handling          │
│ - Watermarking                 │
└────────┬───────────────────────┘
         ▼
┌────────────────────────────────┐
│ MinIO (Object Storage)         │
│ - Parquet format               │
│ - Partitioned by time          │
│ - Raw streaming layer          │
└────────┬───────────────────────┘
         ▼
┌────────────────────────────────┐
│ Spark Compaction Job            │
│ - File consolidation           │
│ - Partition overwrite          │
└────────┬───────────────────────┘
         ▼
┌────────────────────────────────┐
│ Analytics Layer                 │
│ - dbt models                    │
│ - DuckDB query engine           │
└────────┬───────────────────────┘
         ▼
┌────────────────────────────────┐
│ Streamlit Dashboard             │
│ - Live trends                   │
│ - Aggregates & KPIs             │
└────────────────────────────────┘

4. Component Breakdown
4.1 Data Simulator

Purpose:
Simulates real-time stock market ticks.

Key Characteristics:

• Generates random price and volume per ticker
• Publishes JSON messages to Kafka
• Designed to mimic real-world tick velocity

Why it exists:
Allows deterministic testing and local development without external data sources.

4.2 Kafka (Ingestion Layer)

Purpose:
Acts as the durable ingestion buffer between producers and consumers.

Responsibilities:

• Decouples data producers from Spark consumers
• Handles burst traffic
• Guarantees message ordering per partition

Topics:

stock-ticks

4.3 Spark Structured Streaming (Processing Layer)

Purpose:
Processes real-time events and writes them to the data lake.

Responsibilities:

• Schema validation
• Timestamp parsing & event-time processing
• Partitioned Parquet writes
• Fault tolerance via checkpoints

Why Structured Streaming:
Provides exactly-once semantics and seamless transition between streaming and batch workloads.

4.4 Object Storage – MinIO (Lakehouse Layer)

Purpose:
Acts as the central, durable storage layer.

Characteristics:

• S3-compatible API
• Stores immutable Parquet files
• Supports time-based partitioning
• Partition Strategy:
  year=YYYY/
    month=MM/
      day=DD/
        hour=HH/


This enables:

• Efficient pruning
• Time-based analytics

Scalable compaction

4.5 Compaction Job (Optimization Layer)

Problem Addressed:
Spark streaming creates many small Parquet files, which degrade query performance.

Solution:
A periodic Spark batch job that:

• Reads a specific partition
• Repartitions data
• Writes fewer, larger Parquet files
• Overwrites only the target partition

Execution:

• Triggered via Airflow DAG
• Runs independently of streaming job

4.6 Orchestration – Apache Airflow

Purpose:
Coordinates batch jobs and future workflows.

Current Usage:

• Schedule compaction job every N minutes
• Monitor job execution
• Centralized operational control

Why Airflow:
Provides visibility, retries, and extensibility for future pipelines (DBT, quality checks).

4.7 Analytics Layer – dbt + DuckDB

Purpose:
Transforms raw Parquet data into analytics-ready datasets.

Responsibilities:

• SQL-based transformations
• Metric computation (min, max, avg)
• Logical modeling of stock trends

Why DuckDB:

• Lightweight
• Columnar execution
• Perfect for local and embedded analytics

4.8 Visualization – Streamlit

Purpose:
Provides real-time insights into processed data.

Features:

• Live price trends per ticker
• Aggregate statistics
• Auto-refreshing UI

5. Failure Handling & Reliability

• Spark checkpoints ensure recovery from failures
• Kafka offsets tracked for ingestion consistency
• Partition-level overwrite prevents global corruption
• Batch compaction isolated from streaming jobs

6. Scalability & Future Enhancements

• Replace MinIO with AWS S3 / GCS
• Scale Kafka partitions
• Deploy Spark on Kubernetes
• Introduce Trino / Athena
• Add data quality & schema evolution checks

7. Key Takeaways

This architecture demonstrates:

• Production-grade streaming design
• Lakehouse thinking
• Clear separation of concerns
• Operational maturity beyond MVPs

🧠 Architectural Mindset

“Good data systems aren’t defined by tools — they’re defined by boundaries, contracts, and trade-offs.”

This project intentionally mirrors how modern data platforms are built in high-performing engineering teams.
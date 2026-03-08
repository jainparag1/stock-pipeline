# ▶️▶️ START / STOP SERVICES — STOCK MARKET STREAMING PLATFORM

This document provides **one canonical place** to start and stop **all services** used in the Stock Market Streaming Platform.  
All commands assume execution from the **project root** unless stated otherwise.

---

## 1️⃣ Infrastructure Services (Kafka, MinIO, Airflow)

### START
```bash
cd infra
docker-compose up -d
```
### STOP
```bash
cd infra
docker-compose down
```
### VERIFY

- Kafka broker running
- MinIO UI → http://localhost:9001
- Airflow UI → http://localhost:8080

---

## 2️⃣ Python Virtual Environment
### START / ACTIVATE
```bash
source venv/bin/activate
```
### STOP / DEACTIVATE
```bash
deactivate
```
---
## 3️⃣ Stock Data Simulator (Kafka Producer)
### START
```bash
cd data_simulator
source ../venv/bin/activate
python produce_ticks.py
```
### STOP
```bash
Ctrl + C
```
Publishes synthetic stock ticks continuously into Kafka.

---

## 4️⃣ Spark Structured Streaming Job

Consumes Kafka events and writes partitioned parquet files to MinIO.

### START
```bash
cd spark_processor
./run_streaming.sh
```
### STOP
```bash
Ctrl + C
```
### RESTART SAFELY
```bash
./run_streaming.sh
```

Uses Spark checkpoints → restart-safe and exactly-once semantics.

---

## 5️⃣ Spark Compaction Job (Manual)

Compacts small parquet files into optimized partitions.

### START
```bash
cd spark_processor
./run_compaction.sh
```
### STOP
```bash
Ctrl + C
```
Job is idempotent and safe to rerun.

---

## 6️⃣ Spark Compaction via Airflow (Automated)

Runs every 2 minutes via Airflow DAG.

### START
```bash
cd infra
docker-compose up -d
```
Then enable DAG in Airflow UI:
```bash
http://localhost:8080
```

### STOP

Pause DAG in Airflow UI
OR
```bash
cd infra
docker-compose down
```
---

## 7️⃣ dbt Analytics Layer (DuckDB)

Builds analytical models on compacted parquet data.

### START (Run Models)
```bash
cd dbt_models
source ../venv/bin/activate
dbt run
```

### STOP
```bash
Ctrl + C
```
DuckDB runs locally — no service shutdown required.

---

## 8️⃣ Streamlit Dashboard
### START
```bash
cd dashboards
source ../venv/bin/activate
streamlit run app.py
```
### STOP
```bash
Ctrl + C
```

### ACCESS
```bash
http://localhost:8501
```
---

## 9️⃣ Full System Shutdown (Clean Exit)
```bash
cd infra
docker-compose down
```

Then stop any remaining local processes:

- Spark streaming
- Data simulator
- Streamlit
- dbt runs

---

## 🔁 Recommended Startup Order

- Infrastructure (Docker)
- Data Simulator
- Spark Streaming
- Airflow (compaction)
- dbt models
- Streamlit dashboard

---
## Single Click Start/Stop All the Services

To start please run the following command from the project root location
<br>
<b>`sh -x start_all.sh`</b>
<br>and to stop please run 
<br>
<b>`sh -x stop_all.sh`</b>

----





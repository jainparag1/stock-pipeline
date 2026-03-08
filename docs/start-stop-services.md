# ▶️▶️ START / STOP SERVICES — STOCK MARKET STREAMING PLATFORM

This document provides **one canonical place** to start and stop **all services** used in the Stock Market Streaming Platform.  
All commands assume execution from the **project root** unless stated otherwise.

---
## Prerequisite 
Please download the following jar files and place them in a jars folder under the root dirctory
```bash
spark-token-provider-kafka-0-10_2.12-3.5.0.jar
stax-api-1.0-2.jar
commons-collections4-4.4.jar
stax2-api-4.2.1.jar
commons-text-1.9.jar
woodstox-core-6.2.4.jar
commons-lang3-3.12.0.jar
re2j-1.6.jar
commons-pool2-2.11.1.jar
commons-configuration2-2.8.0.jar
core-default.xml
hadoop-auth-3.3.6.jar
hadoop-common-3.3.6.jar
hadoop-hdfs-client-3.3.6.jar
hadoop-hdfs-3.3.6.jar
hadoop-mapreduce-client-core-3.3.6.jar
hadoop-client-3.3.6.jar
hadoop-aws-3.3.6.jar
hadoop-client-runtime-3.3.6.jar
aws-java-sdk-bundle-1.12.523.jar
spark-sql-kafka-0-10_2.12-3.5.0.jar
kafka-clients-3.5.1.jar
```
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






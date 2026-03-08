#!/bin/bash

echo "========================================="
echo " Starting Stock Market Streaming Platform"
echo "========================================="

PROJECT_ROOT=$(pwd)

echo ""
echo "1️. Starting infrastructure (Kafka, MinIO, Airflow)..."
# cd infra
docker-compose -f infra/docker-compose.yml up -d
cd "$PROJECT_ROOT"

# echo ""
# echo "2️. Activating Python virtual environment..."
# python3 -m venv venv
# source venv/bin/activate
# sleep for 5 seconds to ensure services are up
sleep 10
echo ""
echo "3. Starting Kafka stock data simulator..."
# cd ../data_simulator
nohup python3 data_simulator/producer.py > ./logs/data_simulator.log 2>&1 &
SIM_PID=$!
cd "$PROJECT_ROOT"

echo "Data simulator started (PID: $SIM_PID)"

echo ""
echo "4. Starting Spark Structured Streaming job..."
# cd ../spark_processor
nohup sh -x spark_processor/bin/run_stream.sh > ./logs/spark_streaming.log 2>&1 &
SPARK_PID=$!
cd "$PROJECT_ROOT"

echo "Spark streaming started (PID: $SPARK_PID)"

# echo ""
# echo "5. Running dbt models..."
# cd dbt_models
# dbt run
# cd "$PROJECT_ROOT"

echo ""
echo "6. Starting Streamlit dashboard..."
# cd ../dashboards
nohup streamlit run dashboards/dashboard_live.py > ./logs/dashboard.log 2>&1 &
DASH_PID=$!
cd "$PROJECT_ROOT"

echo "Dashboard started (PID: $DASH_PID)"

echo ""
echo "========================================="
echo " Platform started successfully..........!"
echo "========================================="

echo ""
echo "Services:"
echo "MinIO Console : http://localhost:9001"
echo "Airflow UI    : http://localhost:8080"
echo "Dashboard     : http://localhost:8501"

echo ""
echo "Logs directory:"
echo "$PROJECT_ROOT/logs"

echo ""
echo "Use stop_all.sh to shut down services."

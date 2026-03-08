#!/bin/bash

echo "========================================="
echo " Stopping Stock Market Streaming Platform"
echo "========================================="

echo ""
echo "Stopping Spark jobs, simulators, dashboards..."

pkill -f producer.py
pkill -f streamlit
pkill -f spark

echo ""
echo "Stopping Docker infrastructure..."

docker-compose -f infra/docker-compose.yml down

echo ""
echo "========================================="
echo " All services stopped.........!"
echo "========================================="

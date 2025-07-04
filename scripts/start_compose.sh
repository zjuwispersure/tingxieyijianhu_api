#!/bin/bash

set -e

# 启动 MySQL
echo "[INFO] 启动 MySQL..."
docker-compose up -d mysql

# 启动 Redis
echo "[INFO] 启动 Redis..."
docker-compose up -d redis

# 等待 MySQL 健康
echo "[INFO] 等待 MySQL 服务健康..."
MAX_RETRIES=30
RETRY_COUNT=0
while ! docker-compose exec mysql mysqladmin ping -h"localhost" --silent; do
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "MySQL 启动超时"
        exit 1
    fi
    echo "等待 MySQL... ($RETRY_COUNT/$MAX_RETRIES)"
done

# 等待 Redis 健康
echo "[INFO] 等待 Redis 服务健康..."
MAX_RETRIES=30
RETRY_COUNT=0
while ! docker-compose exec redis redis-cli ping | grep -q PONG; do
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Redis 启动超时"
        exit 1
    fi
    echo "等待 Redis... ($RETRY_COUNT/$MAX_RETRIES)"
done

# 启动 API 服务
echo "[INFO] 启动 API 服务..."
docker-compose up -d yuwen

echo "[SUCCESS] 所有服务已启动"

echo "[INFO] 实时查看 yuwen 服务日志 (按 Ctrl+C 退出)..."
docker-compose logs -f yuwen

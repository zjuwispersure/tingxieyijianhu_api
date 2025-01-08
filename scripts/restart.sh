#!/bin/bash

# 停止所有服务
echo "Stopping services..."
docker-compose down

# 删除数据卷（可选，如果需要重置数据）
if [ "$1" = "--reset-data" ]; then
    echo "Removing data volumes..."
    docker volume rm yuwen_mysql_data || true
    rm -rf migrations/versions/*
fi

# 重新构建镜像（如果代码有更新）
if [ "$1" = "--build" ]; then
    echo "Rebuilding images..."
    docker-compose build
fi

# 启动服务
echo "Starting services..."
docker-compose up -d

# 等待 MySQL 服务就绪
echo "Waiting for MySQL to be ready..."
sleep 10

# 等待 API 服务就绪
echo "Waiting for API service..."
MAX_RETRIES=30
RETRY_COUNT=0

while ! curl -s http://localhost:5000/health > /dev/null && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Waiting for API service... ($(( RETRY_COUNT + 1 ))/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$(( RETRY_COUNT + 1 ))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: API service failed to start"
    docker-compose logs api
    exit 1
fi

echo "API service is ready"
sleep 2  # 给应用一点额外时间完全启动

# 如果需要重置数据，执行数据库初始化
if [ "$1" = "--reset-data" ]; then
    echo "Initializing database..."
    # 初始化迁移
    docker-compose exec api flask db init || true
    docker-compose exec api flask db migrate -m "Initial migration"
    docker-compose exec api flask db upgrade
    
    # 导入基础数据
    docker-compose exec api python scripts/import_yuwen_data.py
fi

# 检查服务状态
echo "Checking service status..."
docker-compose ps

echo "Restart completed!" 
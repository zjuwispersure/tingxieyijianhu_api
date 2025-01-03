#!/bin/bash

# 停止所有服务
docker-compose down

# 删除数据卷
docker volume rm yuwen_mysql_data || true

# 删除迁移文件
rm -rf migrations/versions/*

# 重新启动服务
docker-compose up -d

# 等待 API 服务启动（此时 MySQL 已经准备好）
echo "Waiting for API service to start..."
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

# 初始化迁移
docker-compose exec api flask db init || true
docker-compose exec api flask db migrate -m "Initial migration"
docker-compose exec api flask db upgrade

# 运行导入脚本
docker-compose exec api python scripts/import_yuwen_data.py 
#!/bin/bash

echo "Cleaning Docker logs..."

# 获取容器 ID
MYSQL_ID=$(docker ps -qf "name=yuwen-mysql")
YUWEN_ID=$(docker ps -qf "name=yuwen-yuwen")

# 清理日志的函数
clean_container_logs() {
    local container_id=$1
    local container_name=$2
    
    if [ -n "$container_id" ]; then
        echo "Cleaning logs for $container_name ($container_id)..."
        
        # 对于 Linux
        if [ -f "/var/lib/docker/containers/$container_id/$container_id-json.log" ]; then
            sudo truncate -s 0 "/var/lib/docker/containers/$container_id/$container_id-json.log"
        # 对于 macOS
        elif [ -d "$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/docker/containers" ]; then
            sudo truncate -s 0 "$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/docker/containers/$container_id/$container_id-json.log"
        else
            echo "Could not find log file for $container_name"
            # 使用 Docker 命令直接清理日志
            docker container inspect $container_id >/dev/null 2>&1 && \
            echo "" > $(docker inspect --format='{{.LogPath}}' $container_id)
        fi
    else
        echo "Container $container_name not found"
    fi
}

# 停止容器
echo "Stopping containers..."
docker-compose down

# 清理各个容器的日志
clean_container_logs "$MYSQL_ID" "mysql"
clean_container_logs "$YUWEN_ID" "yuwen"

# 重启容器
echo "Restarting containers..."
docker-compose up -d

# 等待服务就绪
echo "Waiting for services to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:5000/health | grep -q '"status":"ok"'; then
        echo "Services are ready!"
        break
    fi
    echo "Waiting for services... ($(( RETRY_COUNT + 1 ))/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$(( RETRY_COUNT + 1 ))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Warning: Services may not be fully ready"
fi

echo "Logs cleaned successfully!" 
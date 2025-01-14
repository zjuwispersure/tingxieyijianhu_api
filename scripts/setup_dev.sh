#!/bin/bash

# 设置错误处理
set -e

# 默认不清理数据库
CLEAN_DB=0

# 解析命令行参数
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --clean-db) CLEAN_DB=1 ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# 输出彩色日志
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 停止所有相关容器
log_info "Stopping all containers..."
docker stop yuwen-api-1 yuwen-mysql-1 yuwen-yuwen-1 yuwen-redis-1 2>/dev/null || true

# 删除所有相关容器
log_info "Removing all containers..."
docker rm yuwen-api-1 yuwen-mysql-1 yuwen-yuwen-1 yuwen-redis-1 2>/dev/null || true

# 根据参数决定是否清理数据库
if [ "$CLEAN_DB" -eq 1 ]; then
    log_info "Cleaning database..."
    docker-compose down -v
else
    log_info "Stopping containers (preserving data)..."
    docker-compose down
fi

# 启动 MySQL
log_info "Starting MySQL..."
docker-compose up -d mysql

# 启动 Redis
log_info "Starting Redis..."
docker-compose up -d redis

# 等待 MySQL 就绪
log_info "Waiting for MySQL to be ready..."
MAX_RETRIES=60  # 增加到 60 次
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec mysql mysql -h 127.0.0.1 -P 3306 -u yuwen -pyuwen123 -e "SELECT 1;" &>/dev/null; then
        log_info "MySQL is ready!"
        break
    fi
    log_warn "Waiting for MySQL... ($(( RETRY_COUNT + 1 ))/$MAX_RETRIES)"
    sleep 5  # 增加到 5 秒
    RETRY_COUNT=$(( RETRY_COUNT + 1 ))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Error: MySQL failed to start"
    docker-compose logs mysql
    exit 1
fi

# 等待 Redis 就绪
log_info "Waiting for Redis to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
        log_info "Redis is ready!"
        break
    fi
    log_warn "Waiting for Redis... ($(( RETRY_COUNT + 1 ))/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$(( RETRY_COUNT + 1 ))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Error: Redis failed to start"
    docker-compose logs redis
    exit 1
fi

# 启动应用服务
log_info "Starting application..."
docker-compose up -d yuwen

# 等待应用就绪
log_info "Waiting for application to be ready..."
MAX_RETRIES=60
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RESPONSE=$(curl -s http://localhost:5000/health || echo "Failed to connect")
    echo "Response: $RESPONSE"
    
    if [[ "$RESPONSE" == *'"status": "ok"'* ]]; then
        log_info "Application is ready!"
        break
    else
        log_warn "Waiting for application... ($(( RETRY_COUNT + 1 ))/$MAX_RETRIES)"
        sleep 5
        RETRY_COUNT=$(( RETRY_COUNT + 1 ))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Error: Application failed to start"
    docker-compose logs yuwen
    exit 1
fi

if [ "$CLEAN_DB" -eq 1 ]; then  
    # 执行数据库迁移
    log_info "Running database migrations..."

    # 等待数据库完全准备好
    sleep 5

    # 执行初始化 SQL 文件
    docker-compose exec -T mysql mysql -u yuwen -pyuwen123 dictation < scripts/sql/init.sql || {
        log_error "Database initialization failed"
        exit 1
    }

    # 验证表是否创建成功
    log_info "Verifying database tables..."
    docker-compose exec -T mysql mysql -u yuwen -pyuwen123 dictation -e "SHOW TABLES;" || {
        log_error "Table verification failed"
        exit 1
    }


# 导入数据
    log_info "Importing data..."
    docker-compose exec -T yuwen python scripts/import_yuwen_data.py || {
    log_error "Data import failed"
    exit 1
}

    # 生成音频
    log_info "Generating audio files..."
    docker-compose exec -T yuwen python scripts/batch_generate_audio.py || {
        log_error "Audio generation failed"
        exit 1
    }

    # 验证表是否创建成功
    log_info "Verifying database tables..."
    docker-compose exec -T yuwen python scripts/check_db.py || {
        log_error "Database verification failed"
        exit 1
    }
fi

log_info "Setup completed successfully!" 
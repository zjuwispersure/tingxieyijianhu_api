#!/bin/bash

# 设置变量
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_FILE="instance/yuwen.db"
BACKUP_FILE="$BACKUP_DIR/yuwen_$TIMESTAMP.db"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 停止应用服务
echo "停止应用服务..."
sudo systemctl stop yuwen

# 备份数据库
echo "备份数据库..."
cp $DB_FILE $BACKUP_FILE

# 压缩备份
echo "压缩备份文件..."
gzip $BACKUP_FILE

# 重启应用服务
echo "重启应用服务..."
sudo systemctl start yuwen

echo "数据库备份完成: ${BACKUP_FILE}.gz"

# 清理旧备份（保留最近7天）
find $BACKUP_DIR -name "yuwen_*.db.gz" -mtime +7 -delete 
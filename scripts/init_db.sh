#!/bin/bash
export FLASK_APP=wsgi.py
export PYTHONPATH=/app
# flask db init
# flask db migrate -m "init"

set -e

cd /app

# 设置 Flask 环境变量
export FLASK_APP=wsgi.py

# 等待 MySQL 就绪
echo "Waiting for MySQL to be ready..."
until nc -z -v -w30 mysql 3306
do
  echo "Waiting for database connection..."
  sleep 5
done

# 初始化数据库
echo "Initializing database..."
flask db upgrade

# 导入语文数据
echo "Importing yuwen data..."
python scripts/import_yuwen_data.py

# 生成音频文件
echo "Generating audio files..."
python scripts/batch_generate_audio.py

echo "Database initialization completed!"

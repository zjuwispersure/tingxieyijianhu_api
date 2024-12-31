#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "开始初始化数据库..."

# 创建数据库目录
mkdir -p instance

# 初始化数据库
echo "创建数据库表..."
flask db upgrade

# 导入基础数据
echo "导入字表数据..."
python scripts/import_characters.py

# 生成音频文件
echo "生成识字表音频..."
python scripts/generate_shizi_audio.py

echo "生成写字表音频..."
python scripts/generate_xiezi_audio.py

echo "生成词语表音频..."
python scripts/generate_ciyu_audio.py

echo "数据库初始化完成！" 
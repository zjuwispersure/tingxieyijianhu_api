#!/bin/bash

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
# .\venv\Scripts\activate  # Windows

# 设置pip镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装依赖
pip install -r requirements.txt

# 检查操作系统并安装 uWSGI（仅在 Linux 上）
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing uWSGI on Linux..."
    pip install uwsgi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "On macOS, skipping uWSGI installation..."
    echo "For development, you can use Flask's built-in server:"
    echo "flask run --host=0.0.0.0 --port=5000"
fi
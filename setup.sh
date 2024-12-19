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
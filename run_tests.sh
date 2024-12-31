#!/bin/bash

# 激活虚拟环境
source .venv/bin/activate

# 安装所有依赖
pip install -r requirements.txt

# 安装测试依赖
pip install pytest pytest-flask pytest-cov

# 添加当前目录到 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# 运行测试并生成覆盖率报告
pytest --cov=app tests/ --cov-report=html 
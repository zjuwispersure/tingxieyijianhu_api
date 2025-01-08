FROM python:3.9-slim

WORKDIR /app

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 使用阿里云的 Debian 镜像源，并移除其他源
RUN rm -f /etc/apt/sources.list.d/*.list && \
    echo "deb http://mirrors.aliyun.com/debian bullseye main non-free contrib" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security bullseye-security main" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian bullseye-updates main non-free contrib" >> /etc/apt/sources.list

# 安装 curl
RUN apt-get update && apt-get install -y curl

# 先复制配置文件
COPY config.py .

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 gunicorn
RUN pip install --no-cache-dir gunicorn==20.1.0

# 复制其余文件
COPY app app/

# 设置 Flask 应用
ENV FLASK_APP=app
ENV PYTHONPATH=/app

# 使用 gunicorn 启动应用
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:5000", "app:create_app()"]
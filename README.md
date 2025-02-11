# 小学生语文词语听写小程序

一个基于 Flask 的小学生语文词语听写系统后端，支持微信登录、家庭群组管理和智能复习功能。

## 功能特性
- 微信小程序授权登录
- 多孩子信息管理
- 家庭群组功能
- 智能听写系统
- 基于遗忘曲线的复习推荐
- 听写结果统计分析

## 技术栈
- Flask 2.0.1
- SQLAlchemy 1.4.23
- JWT 认证
- MySQL 数据库
- WSGI + Docker 部署

## API 文档



## 数据库操作说明

### 1. 数据库初始化
首次部署时需要执行以下步骤：
``` bash
生成初始化脚本
python scripts/generate_db_script.py
复制脚本到服务器
scp scripts/init_db.sh user@server:/path/to/project/scripts/
scp scripts/backup_db.sh user@server:/path/to/project/scripts/
设置执行权限
chmod +x scripts/init_db.sh
chmod +x scripts/backup_db.sh
执行初始化脚本（会自动创建表、导入数据、生成音频）
./scripts/init_db.sh
```

### 2. 数据库备份
建议设置定时备份任务：
``` bash
设置备份脚本权限
chmod +x scripts/backup_db.sh
添加定时任务（每天凌晨3点执行备份）
crontab -e
0 3 /path/to/project/scripts/backup_db.sh
```

### 3. 生成音频
generate_yuwen_audio.py用来生成语文教材音频

### 4. 导入语文教材数据
import_yuwen_data.py用来导入语文教材数据，生成音频，并导入到数据库

## 环境配置

1. 复制环境变量模板
```bash
cp .env.example .env
```

2. 修改 .env 文件，填入实际的配置值：
- 基础配置
  - SECRET_KEY: Flask 密钥
  - JWT_SECRET_KEY: JWT 加密密钥
  
- 数据库配置
  - MYSQL_ROOT_PASSWORD: MySQL root密码
  - MYSQL_USER: 数据库用户名
  - MYSQL_PASSWORD: 数据库密码
  - MYSQL_DATABASE: 数据库名
  
- 微信配置
  - WX_APP_ID: 微信小程序 APP ID
  - WX_APP_SECRET: 微信小程序 APP Secret
  
- Redis配置
  - REDIS_URL: Redis连接URL

3. 启动服务
```bash
docker-compose up -d
```

注意：确保敏感配置信息只存在于 .env 文件中，且不要提交到版本控制系统。

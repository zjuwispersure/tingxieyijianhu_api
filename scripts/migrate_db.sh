#!/bin/bash

# 设置数据库连接信息
DB_USER=yuwen
DB_PASS=yuwen123
DB_NAME=dictation

# 执行 SQL 迁移
docker-compose exec -T mysql mysql -u${DB_USER} -p${DB_PASS} ${DB_NAME} < scripts/sql/migrations/202502111_add_dictation_stats_fields.sql

# 验证迁移
docker-compose exec mysql mysql -u${DB_USER} -p${DB_PASS} ${DB_NAME} -e "DESC dictation_sessions; DESC dictation_details;" 
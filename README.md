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
- uWSGI + Docker 部署

## API 文档

### 用户管理

#### 微信登录
- 接口：`POST /api/login`
- 功能：微信授权登录
- 参数：  ```json
  {
    "code": "wx_code"  // 微信登录code
  }  ```
- 返回：  ```json
  {
    "access_token": "jwt_token"
  }  ```

#### 获取用户信息
- 接口：`GET /api/user`
- 功能：获取当前登录用户信息
- 需要认证：是
- 返回：  ```json
  {
    "id": 1,
    "nickname": "用户昵称",
    "avatar": "头像URL"
  }  ```

### 孩子管理

#### 创建孩子信息
- 接口：`POST /api/child`
- 功能：创建孩子信息
- 需要认证：是
- 参数：  ```json
  {
    "nickname": "小明",
    "school_province": "北京",
    "school_city": "北京",
    "grade": "三年级",
    "semester": "上学期",
    "textbook_version": "人教版"
  }  ```

#### 获取孩子列表
- 接口：`GET /api/children`
- 功能：获取当前用户的所有孩子信息
- 需要认证：是

#### 更新孩子信息
- 接口：`PUT /api/child/:id`
- 功能：更新指定孩子信息
- 需要认证：是

#### 删除孩子信息
- 接口：`DELETE /api/child/:id`
- 功能：删除指定孩子信息
- 需要认证：是

### 家庭群组

#### 创建家庭群组
- 接口：`POST /api/family`
- 功能：创建家庭群组
- 需要认证：是
- 参数：  ```json
  {
    "name": "我的家庭"
  }  ```

#### 邀请成员
- 接口：`POST /api/family/invite`
- 功能：邀请家庭成员
- 需要认证：是
- 参数：  ```json
  {
    "user_id": 123
  }  ```

#### 获取成员列表
- 接口：`GET /api/family/members`
- 功能：获取家庭成员列表
- 需要认证：是

### 听写功能

#### 创建单元听写任务
- 接口：`POST /api/dictation/yuwen/by_unit`
- 功能：创建基于单元的听写任务
- 需要认证：是
- 参数：  ```json
  {
    "child_id": 1,
    "unit": 5,
    "grade": 4,
    "semester": 1,
    "config": {
      "audio_play_count": 2,
      "audio_interval": 3,
      "words_per_dictation": 10
    }
  }  ```

#### 创建智能听写任务
- 接口：`POST /api/dictation/yuwen/smart`
- 功能：基于记忆曲线创建智能复习听写任务
- 需要认证：是
- 参数：  ```json
  {
    "child_id": 1,
    "config": {
      "audio_play_count": 2,
      "audio_interval": 3,
      "words_per_dictation": 10
    }
  }  ```

#### 获取听写任务详情
- 接口：`GET /api/dictation/tasks/<task_id>`
- 功能：获取听写任务信息和词语列表
- 需要认证：是
- 返回：  ```json
  {
    "task_id": 123,
    "words": [
      {
        "id": 1,
        "word": "人声鼎沸",
        "unit": 1,
        "audio_url": "/audio/词语/人声鼎沸.mp3"
      }
    ],
    "config": {
      "audio_play_count": 2,
      "audio_interval": 3,
      "words_per_dictation": 10
    }
  }  ```

#### 提交听写结果
- 接口：`POST /api/dictation/sessions/<session_id>/submit`
- 功能：提交单个词语的听写结果
- 需要认证：是
- 参数：  ```json
  {
    "word_id": 1,
    "user_input": "人声顶沸",
    "writing_order": "1,2,3,4",
    "image_path": "/uploads/dictation/123.jpg"
  }  ```

#### 批改听写结果
- 接口：`POST /api/dictation/details/<detail_id>/correct`
- 功能：批改听写结果
- 需要认证：是
- 参数：  ```json
  {
    "is_correct": false,
    "correction_note": "第三个字写错了，是'鼎'不是'顶'"
  }  ```

#### 开始听写
- 接口：`POST /api/dictation`
- 功能：开始新的听写
- 需要认证：是
- 参数：  ```json
  {
    "child_id": 1,
    "mode": "normal",
    "word_count": 10,
    "repeat_count": 2,
    "interval": 5,
    "prioritize_errors": false
  }  ```

#### 提交结果
- 接口：`POST /api/dictation/:id/result`
- 功能：提交听写结果
- 需要认证：是
- 参数：  ```json
  {
    "result": [
      {
        "word": "测试",
        "is_correct": true
      }
    ]
  }  ```

#### 获取统计
- 接口：`GET /api/dictation/statistics/:id`
- 功能：获取听写统计信息
- 需要认证：是


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

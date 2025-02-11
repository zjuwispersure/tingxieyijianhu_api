#!/bin/bash

# 获取token
echo "Getting token..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code":"test_code_1"}')
TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.data.access_token')

# 开始听写
echo "Starting dictation..."
START_RESPONSE=$(curl -s -X POST http://localhost:5000/dictation/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "child_id": 1,
    "name": "第一单元听写",
    "items": [561]
  }')

# 获取task_id和task_item_id
TASK_ID=$(echo $START_RESPONSE | jq -r '.data.task_id')

# 提交结果
echo "Submitting results..."
curl -s -X POST http://localhost:5000/dictation/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"task_id\": $TASK_ID,
    \"config\": {
      \"time_spent\": 300,
      \"start_time\": \"2025-01-17T11:30:00Z\",
      \"end_time\": \"2025-01-17T11:35:00Z\"
    },
    \"results\": [
      {
        \"yuwen_item_id\": 561,
        \"word\": \"奇观\",
        \"is_correct\": true
      }
    ]
  }" | jq '.'

  
# ## 调试 token 信息 #####################################################
# curl -X GET http://localhost:5000/debug-token \
#   -H "Authorization: Bearer ${your_token}"

# ## 获取孩子总数 #######################################################
# curl -v -X GET http://localhost:5000/child/count \
#   -H "Authorization: Bearer ${your_token}"

# ## 检查昵称是否可用 ###################################################
# curl -X GET "http://localhost:5000/child/check-nickname?nickname=test" \
#   -H "Authorization: Bearer ${your_token}"
 
# ## 添加孩子信息 #######################################################
# curl -X POST 'http://127.0.0.1:5000/family/child/add' \
#   -H 'Content-Type: application/json' \
#   -H "Authorization: Bearer ${your_token}" \
#   -d '{"nickname":"test1","province":"北京市","city":"北京市","grade":1,"semester":1,"textbook_version":"rj"}' 

# ## 更新听写配置 #######################################################
# curl -X POST 'http://127.0.0.1:5000/dictation/config/update' \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer ${your_token}" \
#   --data-binary '{"child_id":1,"words_per_dictation":10,"review_days":3,"dictation_interval":5,"dictation_ratio":100,"wrong_words_only":false}' \

# ## 获取听写配置 #######################################################
# curl -X GET 'http://127.0.0.1:5000/dictation/config/get?child_id=3' \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer ${your_token}" 

# 先获取并打印完整的登录响应
LOGIN_RESPONSE=$(curl -s -f -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code":"test_code"}')
echo "Login response: $LOGIN_RESPONSE"

# 提取 token
your_token=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token')
echo "Extracted token: $your_token"

curl -X GET http://localhost:5000/debug-token \
  -H "Authorization: Bearer ${your_token}"

# 使用 token 访问
curl -v -X GET http://localhost:5000/child/count \
  -H "Authorization: Bearer ${your_token}"

curl -X GET "http://localhost:5000/child/check-nickname?nickname=test" \
  -H "Authorization: Bearer ${your_token}"
 


curl -X POST 'http://127.0.0.1:5000/family/child/add' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${your_token}" \
  -d '{"nickname":"test1","province":"北京市","city":"北京市","grade":1,"semester":1,"textbook_version":"rj"}' 



curl -X POST 'http://127.0.0.1:5000/dictation/config/update' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${your_token}" \
  --data-binary '{"child_id":1,"words_per_dictation":10,"review_days":3,"dictation_interval":5,"dictation_ratio":100,"wrong_words_only":false}' \


curl -X GET 'http://127.0.0.1:5000/dictation/config/get?child_id=3' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${your_token}" 

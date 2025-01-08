
your_token=$(curl -s -f -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code":"test_code"}' | jq -r '.data.access_token')

echo "Token: $your_token"

curl -X GET http://localhost:5000/child/count \
  -H "Authorization: Bearer ${your_token}"

curl -X GET "http://localhost:5000/child/check-nickname?nickname=test" \
  -H "Authorization: Bearer ${your_token}"



curl -X POST 'http://127.0.0.1:5000/child/create' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${your_token}" \
  -d '{"nickname":"test","province":"北京市","city":"北京市","grade":1,"semester":1,"textbook_version":"rj"}' 


curl -X POST http://127.0.0.1:5000/child/create \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${your_token}" \
  -d '{"nickname":"test","province":"北京市","city":"北京市","grade":1,"semester":1,"textbook_version":"rj"}'



curl 'http://127.0.0.1:5000/dictation/config/update' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${your_token}" \
  --data-binary '{"child_id":3,"words_per_dictation":10,"review_days":3,"dictation_interval":5,"dictation_ratio":100,"wrong_words_only":false}' \

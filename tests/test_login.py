import requests
import json

def test_login():
    # 测试登录接口
    url = 'http://localhost:5000/login'
    data = {
        'code': 'test_code'
    }
    
    response = requests.post(url, json=data)
    print('Status Code:', response.status_code)
    print('Response:', json.dumps(response.json(), indent=2))
    
    # 如果登录成功，测试用户信息接口
    if response.status_code == 200:
        token = response.json()['data']['access_token']
        
        # 测试获取用户信息
        headers = {'Authorization': f'Bearer {token}'}
        user_info = requests.get(
            'http://localhost:5000/user/info',
            headers=headers
        )
        print('\nUser Info:', json.dumps(user_info.json(), indent=2))

def test_login_same_user():
    """测试相同用户多次登录"""
    client = app.test_client()
    
    # 第一次登录
    response1 = client.post('/login', json={
        'code': 'test_code_1',
        'userInfo': {
            'nickName': 'Test User',
            'avatarUrl': 'http://test.com/avatar.jpg'
        }
    })
    assert response1.status_code == 200
    data1 = response1.get_json()
    user_id1 = data1['data']['user']['id']
    
    # 第二次登录（使用相同的 code）
    response2 = client.post('/login', json={
        'code': 'test_code_1',
        'userInfo': {
            'nickName': 'Test User Updated',
            'avatarUrl': 'http://test.com/new_avatar.jpg'
        }
    })
    assert response2.status_code == 200
    data2 = response2.get_json()
    user_id2 = data2['data']['user']['id']
    
    # 验证是同一个用户
    assert user_id1 == user_id2

if __name__ == '__main__':
    test_login() 
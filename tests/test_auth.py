import pytest
from app.models.user import User

def test_login_without_code(client):
    """测试没有提供code的登录请求"""
    response = client.post('/api/login')
    assert response.status_code == 400
    assert b'code' in response.data

def test_login_with_invalid_code(client):
    """测试无效code的登录请求"""
    response = client.post('/api/login', json={'code': 'invalid_code'})
    assert response.status_code == 401
    assert b'error' in response.data

def test_login_success(client, mocker):
    """测试成功登录"""
    # Mock 微信API响应
    mock_response = mocker.patch('requests.get')
    mock_response.return_value.json.return_value = {
        'openid': 'test_openid'
    }
    
    response = client.post('/api/login', json={'code': 'valid_code'})
    assert response.status_code == 200
    assert 'access_token' in response.json 
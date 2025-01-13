import pytest
from app.models.user import User
from app.models.child import Child

def test_get_user_without_token(client):
    """测试未认证的用户信息请求"""
    response = client.get('/user')
    assert response.status_code == 401

def test_get_user(client, auth_token):
    """测试获取用户信息"""
    response = client.get('/user', headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert 'id' in response.json

def test_create_child(client, auth_token):
    """测试创建孩子信息"""
    child_data = {
        'nickname': 'Test Child',
        'school_province': '北京',
        'school_city': '北京',
        'grade': '三年级',
        'semester': '上学期',
        'textbook_version': '人教版'
    }
    
    response = client.post(
        '/child',
        json=child_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert response.json['nickname'] == child_data['nickname'] 
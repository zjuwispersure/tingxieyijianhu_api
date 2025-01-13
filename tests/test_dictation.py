import pytest
from app.models.dictation import Dictation

def test_start_dictation(client, auth_token, test_child):
    """测试开始听写"""
    dictation_data = {
        'child_id': test_child.id,
        'mode': 'normal',
        'word_count': 10,
        'repeat_count': 2,
        'interval': 5,
        'prioritize_errors': False
    }
    
    response = client.post(
        '/dictation',
        json=dictation_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert 'id' in response.json
    assert len(response.json['content']) == dictation_data['word_count']

def test_submit_result(client, auth_token, test_dictation):
    """测试提交听写结果"""
    result_data = {
        'result': [
            {'word': '测试', 'is_correct': True},
            {'word': '单词', 'is_correct': False}
        ]
    }
    
    response = client.post(
        f'/dictation/{test_dictation.id}/result',
        json=result_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert response.json['result'] == result_data['result'] 
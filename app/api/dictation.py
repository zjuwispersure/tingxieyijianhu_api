from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.dictation import Dictation
from ..utils.forgetting_curve import calculate_review_words
from ..extensions import db

dictation_bp = Blueprint('dictation', __name__)

@dictation_bp.route('/dictation', methods=['POST'])
@jwt_required()
def start_dictation():
    """开始听写"""
    data = request.get_json()
    
    dictation = Dictation(
        child_id=data['child_id'],
        mode=data['mode'],
        word_count=data['word_count'],
        repeat_count=data['repeat_count'],
        interval=data['interval'],
        prioritize_errors=data['prioritize_errors']
    )
    
    # 根据遗忘曲线算法选择单词
    words = calculate_review_words(data['child_id'], data['word_count'])
    dictation.content = words
    
    db.session.add(dictation)
    db.session.commit()
    
    return jsonify(dictation.to_dict())

@dictation_bp.route('/dictation/<int:id>', methods=['GET'])
@jwt_required()
def get_dictation(id):
    """获取听写内容"""
    dictation = Dictation.query.get_or_404(id)
    return jsonify(dictation.to_dict())

@dictation_bp.route('/dictation/<int:id>/result', methods=['POST'])
@jwt_required()
def submit_result(id):
    """提交听写结果"""
    dictation = Dictation.query.get_or_404(id)
    data = request.get_json()
    
    dictation.result = data['result']
    db.session.commit()
    
    return jsonify(dictation.to_dict())

@dictation_bp.route('/dictation/statistics/<int:id>', methods=['GET'])
@jwt_required()
def get_statistics(id):
    """获取听写统计信息"""
    dictation = Dictation.query.get_or_404(id)
    
    # 计算正确率等统计信息
    stats = {
        'total_words': len(dictation.content),
        'correct_count': sum(1 for r in dictation.result if r['is_correct']),
        'error_count': sum(1 for r in dictation.result if not r['is_correct']),
        'created_at': dictation.created_at
    }
    
    return jsonify(stats)

@dictation_bp.route('/dictation/push', methods=['POST'])
@jwt_required()
def push_result():
    """推送听写结果给家庭群组成员"""
    data = request.get_json()
    dictation_id = data['dictation_id']
    
    dictation = Dictation.query.get_or_404(dictation_id)
    
    # TODO: 实现推送逻辑，可以使用WebSocket或者微信消息推送
    
    return jsonify({'message': '推送成功'}) 
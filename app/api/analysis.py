from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.utils.decorators import log_api_call
from ..models import Child, DictationSession, DictationDetail, YuwenItem
from ..extensions import db
from ..utils.logger import logger
from ..utils.error_codes import *
import traceback
from sqlalchemy import func, case
from datetime import datetime, timedelta

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis/error-pattern', methods=['GET'])
@jwt_required()
@log_api_call
def get_error_pattern():
    """获取错误模式分析
    
    请求参数:
    - child_id: 必填，孩子ID
    - days: 选填，分析天数（默认30天）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "total_errors": 100,
            "error_types": [{
                "type": "similar_char",
                "name": "形近字",
                "count": 30,
                "percentage": 0.3,
                "examples": [{
                    "word": "休",
                    "wrong_input": "体",
                    "frequency": 5
                }]
            }],
            "difficult_words": [{
                "word": "你好",
                "error_count": 5,
                "total_count": 8,
                "error_rate": 0.625,
                "last_wrong": "2024-01-07T12:00:00Z"
            }]
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400

        user_id = get_jwt_identity() 
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=child_id,
            user_id=int(user_id)
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        start_date = datetime.now() - timedelta(days=days)
        
        # 获取错误数据
        errors = DictationDetail.query.join(
            DictationSession
        ).filter(
            DictationSession.child_id == child_id,
            DictationSession.created_at >= start_date,
            DictationDetail.is_correct == False
        ).all()
        
        total_errors = len(errors)
        
        # 分析错误类型
        error_types = {
            'similar_char': {'name': '形近字', 'count': 0, 'examples': {}},
            'similar_sound': {'name': '音近字', 'count': 0, 'examples': {}},
            'missing_char': {'name': '漏字', 'count': 0, 'examples': {}},
            'extra_char': {'name': '多字', 'count': 0, 'examples': {}}
        }
        
        for error in errors:
            error_type = analyze_error_type(error.word, error.user_input)
            if error_type in error_types:
                error_types[error_type]['count'] += 1
                key = f"{error.word}|{error.user_input}"
                error_types[error_type]['examples'][key] = error_types[error_type]['examples'].get(key, 0) + 1
                
        # 获取高频错误词
        difficult_words = DictationDetail.query.join(
            DictationSession
        ).filter(
            DictationSession.child_id == child_id,
            DictationSession.created_at >= start_date
        ).group_by(
            DictationDetail.word
        ).having(
            func.count(DictationDetail.id) >= 3,
            func.sum(case([(DictationDetail.is_correct == False, 1)], else_=0)) / func.count(DictationDetail.id) >= 0.4
        ).with_entities(
            DictationDetail.word,
            func.sum(case([(DictationDetail.is_correct == False, 1)], else_=0)).label('error_count'),
            func.count(DictationDetail.id).label('total_count'),
            func.max(case([(DictationDetail.is_correct == False, DictationDetail.created_at)])).label('last_wrong')
        ).order_by(
            func.sum(case([(DictationDetail.is_correct == False, 1)], else_=0)).desc()
        ).limit(10).all()
        
        # 格式化返回数据
        error_type_list = []
        for type_key, type_data in error_types.items():
            if type_data['count'] > 0:
                examples = []
                for key, freq in sorted(
                    type_data['examples'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]:
                    word, wrong = key.split('|')
                    examples.append({
                        'word': word,
                        'wrong_input': wrong,
                        'frequency': freq
                    })
                    
                error_type_list.append({
                    'type': type_key,
                    'name': type_data['name'],
                    'count': type_data['count'],
                    'percentage': type_data['count'] / total_errors if total_errors else 0,
                    'examples': examples
                })
                
        return jsonify({
            'status': 'success',
            'data': {
                'total_errors': total_errors,
                'error_types': error_type_list,
                'difficult_words': [{
                    'word': word.word,
                    'error_count': word.error_count,
                    'total_count': word.total_count,
                    'error_rate': word.error_count / word.total_count,
                    'last_wrong': word.last_wrong.isoformat() if word.last_wrong else None
                } for word in difficult_words]
            }
        })
        
    except Exception as e:
        logger.error(f"获取错误模式分析失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

def analyze_error_type(correct, wrong):
    """分析错误类型
    
    Args:
        correct: 正确答案
        wrong: 错误答案
        
    Returns:
        str: 错误类型
    """
    if not wrong:
        return 'missing_char'
        
    if len(wrong) > len(correct):
        return 'extra_char'
        
    # TODO: 实现形近字和音近字的判断逻辑
    return 'similar_char' 
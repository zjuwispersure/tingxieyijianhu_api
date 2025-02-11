from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required,get_jwt_identity

from app.utils.decorators import log_api_call
from ..models import Child, DictationSession, DictationDetail, YuwenItem
from ..extensions import db
from ..utils.logger import logger
from ..utils.error_codes import *
import traceback
from sqlalchemy import func, case, Integer
from datetime import datetime, timedelta

report_bp = Blueprint('report', __name__)

@report_bp.route('/report/daily', methods=['GET'])
@jwt_required()
@log_api_call
def get_daily_report():
    """获取每日学习报告
    
    请求参数:
    - child_id: 必填，孩子ID
    - date: 选填，日期(YYYY-MM-DD)，默认今天
    
    返回数据:
    {
        "status": "success",
        "data": {
            "report": {
                "date": "2024-01-07",
                "total_tasks": 5,
                "total_words": 50,
                "accuracy_rate": 0.85,
                "time_spent": 3600,
                "new_words": 20,
                "review_words": 30,
                "mastered_words": 15,
                "difficult_words": [{
                    "word": "你好",
                    "error_count": 3,
                    "total_count": 5
                }]
            }
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        child_id = request.args.get('child_id', type=int)
        date_str = request.args.get('date')
        
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400
            
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
            
        # 解析日期
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        except ValueError:
            return jsonify({
                'status': 'error',
                'code': INVALID_PARAM_VALUE,
                'message': get_error_message(INVALID_PARAM_VALUE, 'date')
            }), 400
            
        # 获取基础统计
        stats = DictationDetail.query.join(
            DictationSession
        ).filter(
            DictationSession.child_id == child_id,
            func.date(DictationSession.created_at) == date
        ).with_entities(
            func.count(DictationDetail.id).label('total_words'),
            func.sum(DictationDetail.is_correct.cast(Integer)).label('correct_words')
        ).first()
        
        # 获取已掌握的词数
        mastered = DictationDetail.query.join(
            DictationSession
        ).filter(
            DictationSession.child_id == child_id,
            func.date(DictationSession.created_at) <= date
        ).group_by(
            DictationDetail.word
        ).having(
            func.sum(DictationDetail.is_correct.cast(Integer)) / func.count(DictationDetail.id) >= 0.8
        ).count()
        
        # 获取困难词
        difficult_words = DictationDetail.query.join(
            DictationSession
        ).filter(
            DictationSession.child_id == child_id,
            func.date(DictationSession.created_at) == date
        ).group_by(
            DictationDetail.word
        ).having(
            func.count(DictationDetail.id) >= 3,
            func.sum(case([(DictationDetail.is_correct == False, 1)], else_=0)) / func.count(DictationDetail.id) >= 0.4
        ).with_entities(
            DictationDetail.word,
            func.sum(case([(DictationDetail.is_correct == False, 1)], else_=0)).label('error_count'),
            func.count(DictationDetail.id).label('total_count')
        ).all()
        
        return jsonify({
            'status': 'success',
            'data': {
                'report': {
                    'date': date.isoformat(),
                    'total_tasks': stats.total_tasks,
                    'total_words': stats.total_words,
                    'accuracy_rate': stats.correct_words / stats.total_words if stats.total_words else 0,
                    'time_spent': stats.time_spent,
                    'new_words': stats.new_words,
                    'review_words': stats.review_words,
                    'mastered_words': mastered,
                    'difficult_words': [{
                        'word': word.word,
                        'error_count': word.error_count,
                        'total_count': word.total_count
                    } for word in difficult_words]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取每日报告失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
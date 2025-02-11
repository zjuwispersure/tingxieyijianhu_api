from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required,get_jwt_identity

from app.utils.decorators import log_api_call
from ..models import Child, DictationSession, DictationDetail, YuwenItem
from ..extensions import db
from ..utils.logger import logger
from ..utils.error_codes import *
import traceback
from sqlalchemy import func, Integer
from datetime import datetime, timedelta

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/progress/overview', methods=['GET'])
@jwt_required()
@log_api_call
def get_progress_overview():
    """获取学习进度概览
    
    请求参数:
    - child_id: 必填，孩子ID
    
    返回数据:
    {
        "status": "success",
        "data": {
            "total_words": 100,        # 总词数
            "learned_words": 80,       # 已学词数
            "mastered_words": 60,      # 已掌握词数
            "learning_days": 30,       # 学习天数
            "total_tasks": 50,         # 总任务数
            "accuracy_rate": 0.85,     # 总正确率
            "daily_average": 10,       # 日均学习词数
            "current_streak": 5,       # 当前连续学习天数
            "longest_streak": 10       # 最长连续学习天数
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400
            
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=child_id,
            user_id=int(get_jwt_identity())
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        # 获取教材总词数
        total_words = YuwenItem.query.filter_by(
            grade=child.grade,
            semester=child.semester,
            textbook_version=child.textbook_version
        ).count()
        
        # 获取学习情况统计
        stats = DictationDetail.query.join(
            DictationSession
        ).filter(
            DictationSession.child_id == child_id
        ).with_entities(
            func.count(func.distinct(DictationDetail.word)).label('learned_words'),
            func.count(DictationDetail.id).label('total_items'),
            func.sum(DictationDetail.is_correct.cast(Integer)).label('correct_items')
        ).first()
        
        # 获取已掌握的词数
        mastered = DictationDetail.query.join(
            DictationSession, YuwenItem
        ).filter(
            DictationSession.child_id == child_id,
            YuwenItem.unit == unit.unit
        ).group_by(
            DictationDetail.word
        ).having(
            func.sum(DictationDetail.is_correct.cast(Integer)) / func.count(DictationDetail.id) >= 0.8
        ).count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_words': total_words,
                'learned_words': stats.learned_words,
                'mastered_words': mastered,
                'accuracy_rate': stats.correct_items / stats.total_items if stats.total_items else 0,
                'completion_rate': stats.learned_words / total_words
            }
        })
        
    except Exception as e:
        logger.error(f"获取学习进度失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 

@progress_bp.route('/progress/units', methods=['GET'])
@jwt_required()
@log_api_call
def get_unit_progress():
    """获取单元学习进度
    
    请求参数:
    - child_id: 必填，孩子ID
    
    返回数据:
    {
        "status": "success",
        "data": {
            "units": [{
                "unit": 1,
                "total_words": 20,
                "learned_words": 15,
                "mastered_words": 10,
                "accuracy_rate": 0.8,
                "completion_rate": 0.75
            }]
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400
            
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=child_id,
            user_id=int(get_jwt_identity())
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        # 获取单元列表
        units = YuwenItem.query.filter_by(
            grade=child.grade,
            semester=child.semester,
            textbook_version=child.textbook_version
        ).with_entities(
            YuwenItem.unit,
            func.count(YuwenItem.id).label('total_words')
        ).group_by(YuwenItem.unit).all()
        
        # 获取每个单元的学习情况
        unit_stats = []
        for unit in units:
            # 获取已学习和掌握的词数
            stats = DictationDetail.query.join(
                DictationSession, YuwenItem
            ).filter(
                DictationSession.child_id == child_id,
                YuwenItem.unit == unit.unit
            ).with_entities(
                func.count(func.distinct(DictationDetail.word)).label('learned_words'),
                func.count(DictationDetail.id).label('total_items'),
                func.sum(DictationDetail.is_correct.cast(Integer)).label('correct_items')
            ).first()
            
            # 获取已掌握的词数
            mastered = DictationDetail.query.join(
                DictationSession, YuwenItem
            ).filter(
                DictationSession.child_id == child_id,
                YuwenItem.unit == unit.unit
            ).group_by(
                DictationDetail.word
            ).having(
                func.sum(DictationDetail.is_correct.cast(Integer)) / func.count(DictationDetail.id) >= 0.8
            ).count()
            
            unit_stats.append({
                'unit': unit.unit,
                'total_words': unit.total_words,
                'learned_words': stats.learned_words,
                'mastered_words': mastered,
                'accuracy_rate': stats.correct_items / stats.total_items if stats.total_items else 0,
                'completion_rate': stats.learned_words / unit.total_words
            })
            
        return jsonify({
            'status': 'success',
            'data': {
                'units': unit_stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取单元进度失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
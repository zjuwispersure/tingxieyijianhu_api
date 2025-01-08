from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required
from ..models import Child, DictationTask, DictationTaskItem, YuwenItem
from ..extensions import db
from ..utils.logger import log_api_call, logger
from ..utils.error_codes import *
import traceback
from sqlalchemy import func
from datetime import datetime, timedelta

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/api/progress/overview', methods=['GET'])
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
            user_id=g.user.id
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
        stats = DictationTaskItem.query.join(
            DictationTask
        ).filter(
            DictationTask.child_id == child_id
        ).with_entities(
            func.count(func.distinct(DictationTaskItem.word)).label('learned_words'),
            func.count(DictationTask.id).label('total_tasks'),
            func.count(DictationTaskItem.id).label('total_items'),
            func.sum(DictationTaskItem.is_correct.cast(Integer)).label('correct_items')
        ).first()
        
        # 获取已掌握的词数（正确率>=80%的词）
        mastered = DictationTaskItem.query.join(
            DictationTask
        ).filter(
            DictationTask.child_id == child_id
        ).group_by(
            DictationTaskItem.word
        ).having(
            func.sum(DictationTaskItem.is_correct.cast(Integer)) / func.count(DictationTaskItem.id) >= 0.8
        ).count()
        
        # 计算学习天数和连续学习天数
        study_dates = db.session.query(
            func.date(DictationTask.created_at).label('date')
        ).filter(
            DictationTask.child_id == child_id
        ).group_by(
            func.date(DictationTask.created_at)
        ).all()
        
        study_dates = [d.date for d in study_dates]
        learning_days = len(study_dates)
        
        # 计算当前连续学习天数
        current_streak = 0
        today = datetime.now().date()
        for i in range(learning_days):
            if (today - timedelta(days=i)).date() in study_dates:
                current_streak += 1
            else:
                break
                
        # 计算最长连续学习天数
        longest_streak = 0
        current = 0
        study_dates.sort()
        
        for i in range(len(study_dates)):
            if i == 0 or (study_dates[i] - study_dates[i-1]).days == 1:
                current += 1
            else:
                longest_streak = max(longest_streak, current)
                current = 1
                
        longest_streak = max(longest_streak, current)
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_words': total_words,
                'learned_words': stats.learned_words,
                'mastered_words': mastered,
                'learning_days': learning_days,
                'total_tasks': stats.total_tasks,
                'accuracy_rate': stats.correct_items / stats.total_items if stats.total_items else 0,
                'daily_average': stats.total_items / learning_days if learning_days else 0,
                'current_streak': current_streak,
                'longest_streak': longest_streak
            }
        })
        
    except Exception as e:
        logger.error(f"获取学习进度概览失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@progress_bp.route('/api/progress/units', methods=['GET'])
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
            user_id=g.user.id
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
            stats = DictationTaskItem.query.join(
                DictationTask, YuwenItem
            ).filter(
                DictationTask.child_id == child_id,
                YuwenItem.unit == unit.unit
            ).with_entities(
                func.count(func.distinct(DictationTaskItem.word)).label('learned_words'),
                func.count(DictationTaskItem.id).label('total_items'),
                func.sum(DictationTaskItem.is_correct.cast(Integer)).label('correct_items')
            ).first()
            
            # 获取已掌握的词数
            mastered = DictationTaskItem.query.join(
                DictationTask, YuwenItem
            ).filter(
                DictationTask.child_id == child_id,
                YuwenItem.unit == unit.unit
            ).group_by(
                DictationTaskItem.word
            ).having(
                func.sum(DictationTaskItem.is_correct.cast(Integer)) / func.count(DictationTaskItem.id) >= 0.8
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
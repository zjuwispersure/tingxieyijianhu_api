from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required,get_jwt_identity
from ..models import Child, DictationTask, DictationTaskItem, YuwenItem
from ..extensions import db
from ..utils.logger import log_api_call, logger
from ..utils.error_codes import *
import traceback
from sqlalchemy import func, Integer,case
from datetime import datetime, timedelta
from ..utils.cache import cache

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/stats/overview', methods=['GET'])
@jwt_required()
@log_api_call
@cache.key_prefix('stats:overview')
def get_overview():
    """获取听写统计概览
    
    请求参数:
    - child_id: 必填，孩子ID
    - days: 选填，统计天数（默认7天）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "total_tasks": 100,
            "total_words": 500,
            "accuracy_rate": 0.85,
            "daily_stats": [{
                "date": "2024-01-07",
                "tasks": 10,
                "words": 50,
                "accuracy": 0.8
            }],
            "word_types": {
                "识字": {
                    "total": 100,
                    "learned": 80,
                    "mastered": 60
                }
            }
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        child_id = request.args.get('child_id', type=int)
        days = request.args.get('days', 7, type=int)
        
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
            
        start_date = datetime.now().date() - timedelta(days=days-1)
        
        # 获取每日统计
        daily_stats = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            stats = DictationTask.query.filter(
                DictationTask.child_id == child_id,
                func.date(DictationTask.created_at) == date
            ).join(DictationTaskItem).with_entities(
                func.count(DictationTask.id).label('tasks'),
                func.count(DictationTaskItem.id).label('words'),
                func.sum(DictationTaskItem.is_correct.cast(Integer)).label('correct')
            ).first()
            
            daily_stats.append({
                'date': date.isoformat(),
                'tasks': stats.tasks,
                'words': stats.words,
                'accuracy': stats.correct / stats.words if stats.words else 0
            })
            
        # 获取总体统计
        total_stats = DictationTask.query.filter(
            DictationTask.child_id == child_id,
            DictationTask.created_at >= start_date
        ).join(DictationTaskItem).with_entities(
            func.count(DictationTask.id).label('total_tasks'),
            func.count(DictationTaskItem.id).label('total_words'),
            func.sum(DictationTaskItem.is_correct.cast(Integer)).label('correct_words')
        ).first()
        
        # 获取各类型词语统计
        word_types = {}
        for type_ in ['识字', '写字', '词语']:
            # 获取总词数
            total = YuwenItem.query.filter_by(
                grade=child.grade,
                semester=child.semester,
                textbook_version=child.textbook_version,
                type=type_
            ).count()
            
            # 获取已学习词数
            learned = DictationTaskItem.query.join(
                DictationTask, YuwenItem
            ).filter(
                DictationTask.child_id == child_id,
                YuwenItem.type == type_
            ).group_by(
                DictationTaskItem.word
            ).count()
            
            # 获取已掌握词数
            mastered = DictationTaskItem.query.join(
                DictationTask, YuwenItem
            ).filter(
                DictationTask.child_id == child_id,
                YuwenItem.type == type_
            ).group_by(
                DictationTaskItem.word
            ).having(
                func.sum(DictationTaskItem.is_correct.cast(Integer)) / func.count(DictationTaskItem.id) >= 0.8
            ).count()
            
            word_types[type_] = {
                'total': total,
                'learned': learned,
                'mastered': mastered
            }
            
        return jsonify({
            'status': 'success',
            'data': {
                'total_tasks': total_stats.total_tasks,
                'total_words': total_stats.total_words,
                'accuracy_rate': total_stats.correct_words / total_stats.total_words if total_stats.total_words else 0,
                'daily_stats': daily_stats,
                'word_types': word_types
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计概览失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@stats_bp.route('/stats/words', methods=['GET'])
@jwt_required()
@log_api_call
def get_word_stats():
    """获取词语统计
    
    请求参数:
    - child_id: 必填，孩子ID
    - type: 选填，类型（识字/写字/词语）
    - unit: 选填，单元号
    - sort: 选填，排序方式(accuracy/frequency/latest)
    - page: 选填，页码（默认1）
    - per_page: 选填，每页数量（默认20）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "words": [{
                "word": "你好",
                "total_count": 5,
                "correct_count": 3,
                "accuracy_rate": 0.6,
                "last_review": "2024-01-07T12:00:00Z"
            }],
            "total": 100,
            "page": 1,
            "pages": 5
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        item_type = request.args.get('type')
        unit = request.args.get('unit', type=int)
        sort = request.args.get('sort', 'latest')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
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
            
        # 构建查询
        query = DictationTaskItem.query.join(
            DictationTask, YuwenItem
        ).filter(
            DictationTask.child_id == child_id
        )
        
        if item_type:
            query = query.filter(YuwenItem.type == item_type)
            
        if unit:
            query = query.filter(YuwenItem.unit == unit)
            
        # 分组统计
        query = query.group_by(
            DictationTaskItem.word
        ).with_entities(
            DictationTaskItem.word,
            func.count(DictationTaskItem.id).label('total_count'),
            func.sum(DictationTaskItem.is_correct.cast(Integer)).label('correct_count'),
            func.max(DictationTaskItem.created_at).label('last_review')
        )
        
        # 排序
        if sort == 'accuracy':
            query = query.order_by(
                (func.sum(DictationTaskItem.is_correct.cast(Integer)) / func.count(DictationTaskItem.id)).desc()
            )
        elif sort == 'frequency':
            query = query.order_by(func.count(DictationTaskItem.id).desc())
        else:  # latest
            query = query.order_by(func.max(DictationTaskItem.created_at).desc())
            
        # 分页
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'status': 'success',
            'data': {
                'words': [{
                    'word': item.word,
                    'total_count': item.total_count,
                    'correct_count': item.correct_count or 0,
                    'accuracy_rate': (item.correct_count or 0) / item.total_count,
                    'last_review': item.last_review.isoformat() if item.last_review else None
                } for item in pagination.items],
                'total': pagination.total,
                'page': page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"获取词语统计失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 

@stats_bp.route('/stats/word-details')
@jwt_required()
@cache.key_prefix('stats:word')
def get_word_details():
    """获取词语详细统计"""
    # ... 现有代码 ... 
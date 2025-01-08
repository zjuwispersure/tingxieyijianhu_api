from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required
from ..models import Child, YuwenItem, DictationTaskItem, DictationTask
from ..extensions import db
from ..utils.logger import log_api_call, logger
from ..utils.error_codes import *
import traceback
from sqlalchemy import func, case

textbook_bp = Blueprint('textbook', __name__)

@textbook_bp.route('/api/textbook/units', methods=['GET'])
@jwt_required()
@log_api_call
def get_units():
    """获取教材单元列表
    
    请求参数:
    - child_id: 必填，孩子ID
    - type: 选填，类型（识字/写字/词语）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "units": [{
                "unit": 1,
                "total_words": 20,
                "learned_words": 15,
                "mastered_words": 10,
                "accuracy_rate": 0.8
            }]
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        item_type = request.args.get('type', '识字')
        
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
            textbook_version=child.textbook_version,
            type=item_type
        ).with_entities(
            YuwenItem.unit,
            func.count(YuwenItem.id).label('total_words')
        ).group_by(
            YuwenItem.unit
        ).all()
        
        # 获取学习情况
        result = []
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
            
            result.append({
                'unit': unit.unit,
                'total_words': unit.total_words,
                'learned_words': stats.learned_words or 0,
                'mastered_words': mastered,
                'accuracy_rate': stats.correct_items / stats.total_items if stats.total_items else 0
            })
            
        return jsonify({
            'status': 'success',
            'data': {
                'units': result
            }
        })
        
    except Exception as e:
        logger.error(f"获取单元列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@textbook_bp.route('/api/textbook/words', methods=['GET'])
@jwt_required()
@log_api_call
def get_words():
    """获取单元词语列表
    
    请求参数:
    - child_id: 必填，孩子ID
    - unit: 必填，单元号
    - type: 选填，类型（识字/写字/词语）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "words": [{
                "id": 1,
                "word": "你好",
                "pinyin": "nǐ hǎo",
                "audio_url": "http://...",
                "learned": true,
                "mastered": false,
                "accuracy_rate": 0.6,
                "last_review": "2024-01-07T12:00:00Z"
            }]
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        unit = request.args.get('unit', type=int)
        item_type = request.args.get('type', '识字')
        
        if not child_id or not unit:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id 和 unit')
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
            
        # 获取词语列表
        words = YuwenItem.query.filter_by(
            grade=child.grade,
            semester=child.semester,
            textbook_version=child.textbook_version,
            type=item_type,
            unit=unit
        ).all()
        
        # 获取学习情况
        result = []
        for word in words:
            # 获取学习情况
            stats = DictationTaskItem.query.join(
                DictationTask
            ).filter(
                DictationTask.child_id == child_id,
                DictationTaskItem.word == word.word
            ).with_entities(
                func.count(DictationTaskItem.id).label('total'),
                func.sum(DictationTaskItem.is_correct.cast(Integer)).label('correct'),
                func.max(DictationTaskItem.created_at).label('last_review')
            ).first()
            
            accuracy_rate = stats.correct / stats.total if stats and stats.total else 0
            
            result.append({
                'id': word.id,
                'word': word.word,
                'pinyin': word.pinyin,
                'audio_url': word.audio_url,
                'learned': bool(stats and stats.total > 0),
                'mastered': bool(accuracy_rate >= 0.8),
                'accuracy_rate': accuracy_rate,
                'last_review': stats.last_review.isoformat() if stats and stats.last_review else None
            })
            
        return jsonify({
            'status': 'success',
            'data': {
                'words': result
            }
        })
        
    except Exception as e:
        logger.error(f"获取词语列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
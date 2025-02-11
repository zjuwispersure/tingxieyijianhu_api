from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.utils.decorators import log_api_call
from ..models import Child, DictationSession, DictationDetail
from ..extensions import db
from ..utils.logger import logger
from ..utils.error_codes import *
import traceback
from sqlalchemy import func, Integer
from datetime import datetime, timedelta

review_bp = Blueprint('review', __name__)

@review_bp.route('/review/words', methods=['GET'])
@jwt_required()
@log_api_call
def get_review_words():
    """获取需要复习的词语
    
    请求参数:
    - child_id: 必填，孩子ID
    - days: 选填，复习天数范围（默认7天）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "words": [{
                "word": "你好",
                "pinyin": "nǐ hǎo",
                "total_count": 5,
                "correct_count": 3,
                "accuracy_rate": 0.6,
                "last_review": "2024-01-07T12:00:00Z"
            }],
            "total_words": 10,
            "mastered_words": 5
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
            
        start_date = datetime.now() - timedelta(days=days)
        
        # 获取需要复习的词语
        words = DictationDetail.query.join(
            DictationSession
        ).filter(
            DictationSession.child_id == child_id,
            DictationSession.created_at >= start_date
        ).group_by(
            DictationDetail.word
        ).with_entities(
            DictationDetail.word,
            func.count(DictationDetail.id).label('total_count'),
            func.sum(DictationDetail.is_correct.cast(Integer)).label('correct_count'),
            func.max(DictationDetail.created_at).label('last_review')
        ).having(
            func.sum(DictationDetail.is_correct.cast(Integer)) / func.count(DictationDetail.id) < 0.8
        ).all()
        
        # 获取词语详细信息
        word_stats = []
        total_words = 0
        mastered_words = 0
        
        for word in words:
            # 获取拼音等信息
            yuwen_item = YuwenItem.query.filter_by(
                word=word.word,
                grade=child.grade,
                semester=child.semester,
                textbook_version=child.textbook_version
            ).first()
            
            if yuwen_item:
                total_words += 1
                accuracy_rate = word.correct_count / word.total_count if word.total_count else 0
                
                if accuracy_rate >= 0.8:
                    mastered_words += 1
                    
                word_stats.append({
                    'word': word.word,
                    'pinyin': yuwen_item.pinyin,
                    'total_count': word.total_count,
                    'correct_count': word.correct_count or 0,
                    'accuracy_rate': accuracy_rate,
                    'last_review': word.last_review.isoformat() if word.last_review else None
                })
                
        return jsonify({
            'status': 'success',
            'data': {
                'words': word_stats,
                'total_words': total_words,
                'mastered_words': mastered_words
            }
        })
        
    except Exception as e:
        logger.error(f"获取复习词语失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@review_bp.route('/review/stats', methods=['GET'])
@jwt_required()
@log_api_call
def get_review_stats():
    """获取复习统计数据
    
    请求参数:
    - child_id: 必填，孩子ID
    - days: 选填，统计天数（默认30天）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "total_reviews": 100,
            "total_words": 500,
            "accuracy_rate": 0.8,
            "daily_stats": [{
                "date": "2024-01-07",
                "reviews": 10,
                "words": 50,
                "accuracy": 0.85
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
            
        # 获取统计数据
        start_date = datetime.now().date() - timedelta(days=days-1)
        daily_stats = []
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            stats = DictationSession.query.filter(
                DictationSession.child_id == child_id,
                func.date(DictationSession.created_at) == date
            ).join(DictationDetail).with_entities(
                func.count(DictationSession.id).label('reviews'),
                func.count(DictationDetail.id).label('words'),
                func.sum(DictationDetail.is_correct.cast(Integer)).label('correct')
            ).first()
            
            daily_stats.append({
                'date': date.isoformat(),
                'reviews': stats.reviews,
                'words': stats.words,
                'accuracy': stats.correct / stats.words if stats.words else 0
            })
            
        # 计算总体统计
        total_stats = DictationSession.query.filter(
            DictationSession.child_id == child_id,
            DictationSession.created_at >= start_date
        ).join(DictationDetail).with_entities(
            func.count(DictationSession.id).label('total_reviews'),
            func.count(DictationDetail.id).label('total_words'),
            func.sum(DictationDetail.is_correct.cast(Integer)).label('correct_words')
        ).first()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_reviews': total_stats.total_reviews,
                'total_words': total_stats.total_words,
                'accuracy_rate': total_stats.correct_words / total_stats.total_words if total_stats.total_words else 0,
                'daily_stats': daily_stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取复习统计失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
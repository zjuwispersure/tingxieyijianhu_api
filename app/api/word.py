from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.utils.decorators import log_api_call
from ..models import Child, YuwenItem, WordLearningStatus
from ..extensions import db
from ..utils.logger import logger
from ..utils.error_codes import *
import traceback
from sqlalchemy.exc import SQLAlchemyError

word_bp = Blueprint('word', __name__)

@word_bp.route('/word/status', methods=['GET'])
@jwt_required()
@log_api_call
def get_word_status():
    """获取词语学习状态
    
    请求参数:
    - child_id: 必填，孩子ID
    - word: 必填，词语
    
    返回数据:
    {
        "status": "success",
        "data": {
            "word": {
                "id": 1,
                "word": "你好",
                "pinyin": "nǐ hǎo",
                "audio_url": "http://...",
                "learned": true,
                "mastered": false,
                "accuracy_rate": 0.6,
                "last_review": "2024-01-07T12:00:00Z",
                "next_review": "2024-01-10T12:00:00Z",
                "learning_stage": 2,
                "review_count": 5
            }
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        child_id = request.args.get('child_id', type=int)
        word = request.args.get('word')
        
        if not child_id or not word:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id 和 word')
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
            
        # 获取词语信息
        yuwen_item = YuwenItem.query.filter_by(word=word).first()
        if not yuwen_item:
            return jsonify({
                'status': 'error',
                'code': RESOURCE_NOT_FOUND,
                'message': get_error_message(RESOURCE_NOT_FOUND)
            }), 404
            
        # 获取学习状态
        status = WordLearningStatus.query.filter_by(
            child_id=child_id,
            word=word
        ).first()
        
        if not status:
            status = WordLearningStatus(
                child_id=child_id,
                word=word
            )
            db.session.add(status)
            db.session.commit()
            
        result = yuwen_item.to_dict()
        result.update(status.to_dict())
        
        return jsonify({
            'status': 'success',
            'data': {
                'word': result
            }
        })
        
    except Exception as e:
        logger.error(f"获取词语状态失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@word_bp.route('/word/status/update', methods=['POST'])
@jwt_required()
@log_api_call
def update_word_status():
    """更新词语学习状态"""
    try:
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        
        try:
            # 验证必要参数
            if not all(k in data for k in ['child_id', 'word', 'yuwen_item_id']):
                return jsonify({
                    'status': 'error',
                    'code': MISSING_REQUIRED_PARAM,
                    'message': get_error_message(MISSING_REQUIRED_PARAM)
                }), 400
            
            # 获取或创建学习状态
            status = WordLearningStatus.query.filter_by(
                child_id=data['child_id'],
                yuwen_item_id=data['yuwen_item_id']
            ).first()
            
            if not status:
                status = WordLearningStatus(
                    child_id=data['child_id'],
                    word=data['word'],
                    yuwen_item_id=data['yuwen_item_id']
                )
            
            # 更新状态
            if 'learning_stage' in data:
                status.learning_stage = data['learning_stage']
            if 'review_count' in data:
                status.review_count = data['review_count']
            if 'next_review' in data:
                status.next_review = data['next_review']
            if 'is_mastered' in data:
                status.is_mastered = data['is_mastered']
            
            db.session.add(status)
            db.session.flush()
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'status': status.to_dict()
                }
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"更新词语状态失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required,get_jwt_identity
from ..models import Child, DictationConfig
from ..extensions import db
from ..utils.logger import log_api_call, logger
from ..utils.error_codes import *
import traceback
from sqlalchemy.exc import SQLAlchemyError

config_bp = Blueprint('config', __name__)

@config_bp.route('/config/dictation/get', methods=['GET'])
@jwt_required()
@log_api_call
def get_dictation_config():
    """获取听写配置
    
    请求参数:
    - child_id: 必填，孩子ID
    
    返回数据:
    {
        "status": "success",
        "data": {
            "config": {
                "words_per_dictation": 10,
                "review_days": 3,
                "dictation_interval": 5,
                "dictation_ratio": 100,
                "wrong_words_only": false
            }
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
            
        config = child.dictation_config
        if not config:
            config = DictationConfig(child=child)
            db.session.add(config)
            db.session.commit()
            
        return jsonify({
            'status': 'success',
            'data': {
                'config': config.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"获取听写配置失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@config_bp.route('/config/dictation/update', methods=['PUT'])
@jwt_required()
@log_api_call
def update_dictation_config():
    """更新听写配置
    
    请求参数:
    {
        "child_id": 1,
        "words_per_dictation": 10,
        "review_days": 3,
        "dictation_interval": 5,
        "dictation_ratio": 100,
        "wrong_words_only": false
    }
    """
    try:
        data = request.get_json()
        if not data or 'child_id' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400
            
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=data['child_id'],
            user_id=int(get_jwt_identity())
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        config = child.dictation_config
        if not config:
            config = DictationConfig(child=child)
            db.session.add(config)
            
        # 更新配置
        for field in [
            'words_per_dictation',
            'review_days',
            'dictation_interval',
            'dictation_ratio',
            'wrong_words_only'
        ]:
            if field in data:
                setattr(config, field, data[field])
                
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"数据库错误: {str(e)}")
            return jsonify({
                'status': 'error',
                'code': DATABASE_ERROR,
                'message': get_error_message(DATABASE_ERROR)
            }), 500
            
        return jsonify({
            'status': 'success',
            'data': {
                'config': config.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"更新听写配置失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
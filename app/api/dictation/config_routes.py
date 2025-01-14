from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required,get_jwt_identity

from app.utils.decorators import log_api_call
from ...models import Child, DictationConfig
from ...extensions import db
from ...utils.logger import logger
from ...utils.error_codes import *
import traceback
from sqlalchemy.exc import SQLAlchemyError
from . import dictation_config_bp

@dictation_config_bp.route('/config/dictation/get', methods=['GET'])
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

@dictation_config_bp.route('/dictation/config/update', methods=['POST'])
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
        # 开启事务
        db.session.begin_nested()
        
        data = request.get_json()
        child_id = data.get('child_id')
        
        config = DictationConfig.query.filter_by(child_id=child_id).first()
        if not config:
            config = DictationConfig(child_id=child_id)
            
        try:
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
            
            db.session.add(config)
            db.session.flush()
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': '配置更新成功'
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"更新听写配置失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
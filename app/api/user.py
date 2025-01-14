from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.utils.decorators import log_api_call
from ..models import User
from ..extensions import db
from ..utils.logger import logger
from ..utils.error_codes import *
import traceback
from sqlalchemy.exc import SQLAlchemyError

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/profile', methods=['GET'])
@jwt_required()
@log_api_call
def get_profile():
    """获取用户信息
    
    返回数据:
    {
        "status": "success",
        "data": {
            "user": {
                "id": 1,
                "nickname": "张三",
                "avatar_url": "http://...",
                "created_at": "2024-01-07T12:00:00Z",
                "last_login": "2024-01-07T12:00:00Z"
            }
        }
    }
    """
    try:
        user = User.query.get(int(get_jwt_identity()))
        if not user:
            return jsonify({
                'status': 'error',
                'code': USER_NOT_FOUND,
                'message': get_error_message(USER_NOT_FOUND)
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@user_bp.route('/user/profile', methods=['PUT'])
@jwt_required()
@log_api_call
def update_profile():
    """更新用户信息
    
    请求参数:
    {
        "nickname": "张三",     # 选填
        "avatar_url": "http://..."  # 选填
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'code': INVALID_REQUEST_FORMAT,
                'message': get_error_message(INVALID_REQUEST_FORMAT)
            }), 400
            
        user = User.query.get(int(get_jwt_identity()))
        if not user:
            return jsonify({
                'status': 'error',
                'code': USER_NOT_FOUND,
                'message': get_error_message(USER_NOT_FOUND)
            }), 404
            
        # 更新信息
        for field in ['nickname', 'avatar_url']:
            if field in data:
                setattr(user, field, data[field])
                
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
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@user_bp.route('/user/settings', methods=['GET'])
@jwt_required()
@log_api_call
def get_settings():
    """获取用户设置
    
    返回数据:
    {
        "status": "success",
        "data": {
            "settings": {
                "notification_enabled": true,
                "sound_enabled": true,
                "theme": "light"
            }
        }
    }
    """
    try:
        user = User.query.get(int(get_jwt_identity()))
        if not user:
            return jsonify({
                'status': 'error',
                'code': USER_NOT_FOUND,
                'message': get_error_message(USER_NOT_FOUND)
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'settings': user.settings
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户设置失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@user_bp.route('/user/settings', methods=['PUT'])
@jwt_required()
@log_api_call
def update_settings():
    """更新用户设置
    
    请求参数:
    {
        "notification_enabled": true,  # 选填
        "sound_enabled": true,         # 选填
        "theme": "light"              # 选填
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'code': INVALID_REQUEST_FORMAT,
                'message': get_error_message(INVALID_REQUEST_FORMAT)
            }), 400
            
        user = User.query.get(int(get_jwt_identity()))
        if not user:
            return jsonify({
                'status': 'error',
                'code': USER_NOT_FOUND,
                'message': get_error_message(USER_NOT_FOUND)
            }), 404
            
        # 更新设置
        settings = user.settings or {}
        for key, value in data.items():
            settings[key] = value
        user.settings = settings
        
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
                'settings': user.settings
            }
        })
        
    except Exception as e:
        logger.error(f"更新用户设置失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
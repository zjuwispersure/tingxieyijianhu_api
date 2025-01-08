from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from ..utils.wx_service import get_openid
from ..models import User
from ..extensions import db
from ..utils.logger import log_api_call
from ..utils.error_codes import *
import traceback
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

from app.utils import logger

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
@log_api_call
def login():
    """微信小程序登录
    
    请求参数:
    {
        "code": "wx_code"
    }
    
    返回数据:
    {
        "status": "success",
        "data": {
            "access_token": "xxx",
            "refresh_token": "xxx",
            "user": {
                "id": 1,
                "nickname": "xxx"
            }
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'code')
            }), 400
            
        code = data['code']
        
        # 测试模式
        if code == 'test_code':
            user = User.query.first()
            if not user:
                user = User(openid='test_openid')
                db.session.add(user)
                db.session.commit()
        else:
            # 获取openid
            openid = get_openid(code)
            if not openid:
                return jsonify({
                    'status': 'error',
                    'code': INVALID_WX_CODE,
                    'message': get_error_message(INVALID_WX_CODE)
                }), 400
                
            # 获取或创建用户
            user = User.query.filter_by(openid=openid).first()
            if not user:
                user = User(openid=openid)
                db.session.add(user)
                db.session.commit()
                
        # 生成token
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'status': 'success',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"登录失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@auth_bp.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
@log_api_call
def refresh_token():
    """刷新访问令牌
    
    请求参数:
    {
        "refresh_token": "xxx"  # 必填，刷新令牌
    }
    
    返回数据:
    {
        "status": "success",
        "data": {
            "access_token": "xxx"
        }
    }
    """
    try:
        # 获取用户ID
        user_id = get_jwt_identity()
        
        # 生成新的访问令牌
        access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'access_token': access_token
            }
        })
        
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
@log_api_call
def logout():
    """退出登录
    
    返回数据:
    {
        "status": "success",
        "message": "退出成功"
    }
    """
    try:
        # TODO: 实现令牌黑名单
        return jsonify({
            'status': 'success',
            'message': '退出成功'
        })
        
    except Exception as e:
        logger.error(f"退出登录失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from ..models import User
from ..utils.error_codes import *
from ..utils.logger import logger
import traceback

def login_required(f):
    """登录验证装饰器
    
    使用 JWT token 验证用户登录状态，并将用户对象存入 g.user
    
    错误返回:
    {
        "status": "error",
        "code": 2001,         # UNAUTHORIZED
        "message": "请先登录"
    }
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'status': 'error',
                    'code': UNAUTHORIZED,
                    'message': get_error_message(UNAUTHORIZED)
                }), 401
            g.user = user
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"认证失败: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'code': UNAUTHORIZED,
                'message': get_error_message(UNAUTHORIZED)
            }), 401
    return decorated_function

def admin_required(f):
    """管理员权限验证装饰器
    
    验证用户是否具有管理员权限
    
    错误返回:
    {
        "status": "error",
        "code": 2003,         # PERMISSION_DENIED
        "message": "没有权限执行此操作"
    }
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 先验证登录
            verify_jwt_in_request()
            
            # 获取用户
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'status': 'error',
                    'code': UNAUTHORIZED,
                    'message': get_error_message(UNAUTHORIZED)
                }), 401
                
            # 验证管理员权限
            if not user.is_admin:
                return jsonify({
                    'status': 'error',
                    'code': PERMISSION_DENIED,
                    'message': get_error_message(PERMISSION_DENIED)
                }), 403
                
            # 将用户对象存入 g
            g.user = user
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"权限验证失败: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'code': PERMISSION_DENIED,
                'message': get_error_message(PERMISSION_DENIED)
            }), 403
            
    return decorated_function

def api_key_required(f):
    """API密钥验证装饰器
    
    用于内部API调用的验证
    
    错误返回:
    {
        "status": "error",
        "code": 2002,         # INVALID_TOKEN
        "message": "无效的API密钥"
    }
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            api_key = request.headers.get('X-API-Key')
            if not api_key or api_key != current_app.config['API_KEY']:
                return jsonify({
                    'status': 'error',
                    'code': INVALID_TOKEN,
                    'message': get_error_message(INVALID_TOKEN)
                }), 401
                
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"API密钥验证失败: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'code': INVALID_TOKEN,
                'message': get_error_message(INVALID_TOKEN)
            }), 401
            
    return decorated_function 

from functools import wraps
from flask import Blueprint, jsonify, request
from app.api.family import jwt_required_with_logger
from app.utils.decorators import log_api_call
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request
from app.utils.logger import logger
from app.utils.error_codes import INTERNAL_ERROR
from app.models.user import User
import traceback

test_bp = Blueprint('test', __name__)
def jwt_required_with_logger():
    """带日志的 JWT 验证装饰器"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            logger.info("Starting token verification...")
            auth_header = request.headers.get('Authorization', '')
            logger.info(f"Auth header: {auth_header}")
            try:
                # 手动验证 JWT
                verify_jwt_in_request()
                user_id = int(get_jwt_identity())
                claims = get_jwt()
                logger.info(f"Token claims: user_id={user_id}, claims={claims}")
                return fn(*args, **kwargs)
            except Exception as e:
                logger.error(f"Token verification failed: {str(e)}\n{traceback.format_exc()}")
                return jsonify({
                    'status': 'error',
                    'code': 2001,
                    'message': '请先登录'
                }), 401
        return decorator
    return wrapper

@test_bp.route('/debug-token', methods=['GET'])
@log_api_call
@jwt_required_with_logger()
def debug_token():
    """调试 JWT token 信息"""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        logger.info(f"Token verification passed in debug_token: user_id={user_id}, claims={claims}")
        
        # 获取用户信息
        user = User.query.get(int(user_id)) if user_id else None
        
        return jsonify({
            'status': 'success',
            'data': {
                'jwt_identity': user_id,
                'jwt_identity_type': type(user_id).__name__,
                'auth_header': request.headers.get('Authorization', ''),
                'user_exists': user is not None,
                'user_id': user.id if user else None
            }
        })
        
    except Exception as e:
        logger.error(f"Token 调试失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': str(e)
        }), 500
from functools import wraps
from flask import request, g, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from ..models import User
from ..utils.error_codes import *
from .logger import logger
import traceback
from ..models.family import UserFamilyRelation
import logging
import time
import json
from sqlalchemy.exc import OperationalError
from time import sleep


def log_api_call(f):
    """记录 API 调用的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        endpoint = request.endpoint
        method = request.method
        url = request.url
        headers = dict(request.headers)
        
        # 获取请求体（如果有）
        try:
            request_data = None
            if request.method == 'GET':
                request_data = dict(request.args)
            elif request.is_json:
                request_data = request.get_json()
            elif request.form:
                request_data = dict(request.form)
                
            # 只在有数据时记录
            if request_data:
                logger.info(f"Request Data: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
                
        except Exception as e:
            logger.warning(f"Error parsing request data: {str(e)}")

        # 记录请求信息
        logger.info(f"API Request - {endpoint} [{method}]:")
        #logger.info(f"URL: {url}")
        #logger.info(f"Headers: {json.dumps(headers, indent=2)}")

        try:
            # 执行原始函数
            response = f(*args, **kwargs)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 记录响应信息
            if hasattr(response, 'json'):
                response_data = response.json
            elif isinstance(response, tuple):
                response_data = response[0].json
            else:
                response_data = response
                
            logger.info(f"API Response - {endpoint} [{method}]:")
            logger.info(f"Status Code: {getattr(response, 'status_code', 200)}")
            logger.info(f"Response Data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            logger.info(f"Execution Time: {execution_time:.3f}s")
            
            return response
            
        except Exception as e:
            # 记录异常信息
            logger.error(f"API Error - {endpoint} [{method}]:")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Execution Time: {time.time() - start_time:.3f}s")
            raise
            
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

def get_user_families(user_id: int) -> list:
    """获取用户所属的所有家庭ID"""
    relations = UserFamilyRelation.query.filter_by(user_id=user_id).all()
    return [relation.family_id for relation in relations]

def get_user_admin_families(user_id: int) -> list:
    """获取用户作为管理员的家庭ID"""
    relations = UserFamilyRelation.query.filter_by(
        user_id=user_id,
        is_admin=True
    ).all()
    return [relation.family_id for relation in relations]

def get_current_family_id() -> int:
    """从 JWT token 中获取当前 family_id"""
    claims = get_jwt()
    return claims.get('family_id')

def require_family_access(func):
    """验证用户是否有权限访问该家庭"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        # 优先使用路径/参数中的 family_id，如果没有则使用 token 中的
        family_id = kwargs.get('family_id') or request.args.get('family_id') or \
                   (request.get_json() or {}).get('family_id') or get_current_family_id()
        
        if not family_id:
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': '未指定family_id'
            }), 400
            
        relation = UserFamilyRelation.query.filter_by(
            user_id=user_id,
            family_id=family_id
        ).first()
        
        if not relation:
            return jsonify({
                'status': 'error',
                'code': 403,
                'message': '无权访问该家庭'
            }), 403
        
        # 将 family_id 存入 g 对象，方便视图函数使用
        g.family_id = family_id
        return func(*args, **kwargs)
    return wrapper

def require_family_admin(func):
    """验证用户是否是家庭管理员"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        family_id = kwargs.get('family_id')
        
        if not family_id:
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': '缺少family_id参数'
            }), 400
            
        relation = UserFamilyRelation.query.filter_by(
            user_id=user_id,
            family_id=family_id,
            is_admin=True
        ).first()
        
        if not relation:
            return jsonify({
                'status': 'error',
                'code': 403,
                'message': '需要家庭管理员权限'
            }), 403
            
        return func(*args, **kwargs)
    return wrapper 

def get_current_user():
    """获取当前登录用户"""
    verify_jwt_in_request()
    user_id = int(get_jwt_identity())
    
    user = User.query.get(user_id)
    if not user:
        return None
    
    return user

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            logger.info("Starting token verification...")
            # 获取 Authorization header
            auth_header = request.headers.get('Authorization', '')
            logger.info(f"Auth header: {auth_header}")
            
            verify_jwt_in_request()
            logger.info("JWT verification passed")
            
            user_id = int(get_jwt_identity())
            claims = get_jwt()
            logger.info(f"Token claims: user_id={user_id}, claims={claims}")
            
            user = User.query.get(user_id)
            if not user:
                logger.warning(f"User not found: user_id={user_id}")
                return jsonify({
                    'status': 'error',
                    'code': 2001,
                    'message': '请先登录'
                }), 401
                
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'code': 2001,
                'message': '请先登录'
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
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            
            if not user:
                return jsonify({
                    'status': 'error',
                    'code': UNAUTHORIZED,
                    'message': get_error_message(UNAUTHORIZED)
                }), 401
                
            if not user.is_admin:
                return jsonify({
                    'status': 'error',
                    'code': PERMISSION_DENIED,
                    'message': get_error_message(PERMISSION_DENIED)
                }), 403
                
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

def with_db_retry(max_retries=3, delay=0.1):
    """数据库操作重试装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except OperationalError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying database operation... (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                    
            logger.error(f"Database operation failed after {max_retries} attempts")
            # 重新抛出异常，让上层错误处理来处理
            raise last_error
            
        return wrapper
    return decorator

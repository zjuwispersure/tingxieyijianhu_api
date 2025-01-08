import requests
from flask import current_app, request, jsonify
from ..utils.error_codes import *
from ..utils.logger import logger
import traceback
from functools import wraps

class WXService:
    """微信服务类
    
    处理微信相关的API调用，包括登录、获取用户信息等
    """
    
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.test_mode = current_app.config.get('TESTING', False)
        
    def get_openid(self, code):
        """通过 code 获取用户 openid
        
        Args:
            code: 微信登录code
            
        Returns:
            str: 用户的openid
            
        Raises:
            WXAPIError: 微信API调用失败
        """
        # 测试环境使用固定的测试 openid
        if self.test_mode:
            if 'wechatdevtools' in request.headers.get('User-Agent', ''):
                return 'test_openid_devtools'  # 开发工具固定返回这个
            return 'test_openid_' + code[-6:]  # 其他测试环境用 code 后6位
            
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': self.app_id,
            'secret': self.app_secret,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            logger.info(f"WX API response: {data}")
            
            if 'openid' not in data:
                error_msg = data.get('errmsg', '未知错误')
                logger.error(f"Failed to get openid: {data}")
                raise WXAPIError(error_msg)
                
            return data['openid']
            
        except requests.RequestException as e:
            logger.error(f"WX API request failed: {str(e)}\n{traceback.format_exc()}")
            raise WXAPIError(f"微信API请求失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error getting openid: {str(e)}\n{traceback.format_exc()}")
            raise WXAPIError(f"获取openid失败: {str(e)}")

class WXAPIError(Exception):
    """微信API错误
    
    用于包装微信API的错误信息，便于统一处理
    """
    
    def __init__(self, message):
        self.message = message
        self.code = WX_API_ERROR
        super().__init__(self.message)
        
    def to_dict(self):
        """转换为API响应格式"""
        return {
            'status': 'error',
            'code': self.code,
            'message': get_error_message(self.code, self.message)
        }

def handle_wx_error(f):
    """微信错误处理装饰器
    
    统一处理微信相关的错误，转换为标准的API响应格式
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except WXAPIError as e:
            response = e.to_dict()
            return jsonify(response), 500
        except Exception as e:
            logger.error(f"微信服务错误: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'code': INTERNAL_ERROR,
                'message': get_error_message(INTERNAL_ERROR)
            }), 500
    return decorated_function 

def get_openid(code):
    """获取微信openid"""
    try:
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': current_app.config['WX_APP_ID'],
            'secret': current_app.config['WX_APP_SECRET'],
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.get(url, params=params)
        data = response.json()
        return data.get('openid')
    except Exception as e:
        logger.error(f"获取openid失败: {str(e)}")
        return None 
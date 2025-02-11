import requests
from flask import current_app, request, jsonify
from ..utils.error_codes import *
from ..utils.logger import logger
import traceback
from functools import wraps
import logging
from typing import Optional

logger = logging.getLogger(__name__)

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
            
        try:
            # 检查配置
            app_id = self.app_id
            app_secret = self.app_secret
            
            logger.info(f"Using APP_ID: {app_id[:6]}...") # 只显示前6位,避免泄露
            if not app_id or not app_secret:
                logger.error("Missing WX_APP_ID or WX_APP_SECRET in configuration")
                raise WXAPIError("微信配置缺失")
            
            url = 'https://api.weixin.qq.com/sns/jscode2session'
            params = {
                'appid': app_id,
                'secret': app_secret,
                'js_code': code,
                'grant_type': 'authorization_code'
            }
            
            # 打印完整请求信息
            logger.info(f"WX API request URL: {url}")
            logger.info(f"WX API request params: {params}")
            
            response = requests.get(url, params=params)
            logger.info(f"WX API full response: {response.text}")
            
            data = response.json()
            if 'openid' not in data:
                error_msg = data.get('errmsg', '未知错误')
                error_code = data.get('errcode')
                logger.error(f"Failed to get openid. Error code: {error_code}, message: {error_msg}")
                # 微信错误码说明
                error_codes = {
                    40029: "code 无效",
                    40163: "code 已被使用",
                    45011: "API 调用太频繁",
                    -1: "系统繁忙"
                }
                error_desc = error_codes.get(error_code, "未知错误")
                logger.error(f"Error description: {error_desc}")
                raise WXAPIError(f"{error_msg} ({error_desc})")
                
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

def get_openid(code: str) -> Optional[str]:
    """通过微信 code 获取 openid"""
    try:
        # 检查配置
        app_id = current_app.config.get('WX_APP_ID')
        app_secret = current_app.config.get('WX_APP_SECRET')
        
        if not app_id or not app_secret:
            logger.error("Missing WX_APP_ID or WX_APP_SECRET in configuration")
            return None
            
        url = f"https://api.weixin.qq.com/sns/jscode2session"
        params = {
            'appid': app_id,
            'secret': app_secret,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        logger.info(f"Calling WeChat API with code: {code}")
        response = requests.get(url, params=params)
        logger.info(f"WeChat API response status: {response.status_code}")
        logger.info(f"WeChat API response content: {response.text}")
        
        if response.status_code != 200:
            logger.error(f"WeChat API request failed with status {response.status_code}")
            return None
            
        data = response.json()
        if 'errcode' in data:
            logger.error(f"WeChat API returned error: {data}")
            return None
            
        return data.get('openid')
        
    except Exception as e:
        logger.error(f"Error getting openid: {str(e)}", exc_info=True)
        return None 
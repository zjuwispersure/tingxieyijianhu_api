import requests
import json
import random
import string
from datetime import datetime
from flask import current_app
from .logger import log_message

class WXService:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.code2session_url = "https://api.weixin.qq.com/sns/jscode2session"

    def get_openid(self, code, use_fallback=False):
        """
        获取微信用户openid
        :param code: 微信登录code
        :param use_fallback: 是否使用临时ID作为fallback
        :return: openid
        """
        try:
            params = {
                'appid': self.app_id,
                'secret': self.app_secret,
                'js_code': code,
                'grant_type': 'authorization_code'
            }
            
            response = requests.get(self.code2session_url, params=params)
            result = response.json()
            
            if 'openid' in result:
                return result['openid']
            
            # 记录错误
            log_message({
                "event": "wx_auth_error",
                "error": result.get('errmsg', 'Unknown error'),
                "code": code
            })
            
            if use_fallback:
                # 生成临时ID
                temp_id = self._generate_temp_id()
                return f"temp_{temp_id}"
            
            raise Exception(f"Failed to get openid: {result.get('errmsg')}")
            
        except Exception as e:
            log_message({
                "event": "wx_auth_critical_error",
                "error": str(e),
                "code": code
            })
            if use_fallback:
                temp_id = self._generate_temp_id()
                return f"temp_{temp_id}"
            raise
    
    def _generate_temp_id(self):
        """生成临时ID"""
        chars = string.ascii_letters + string.digits
        random_str = ''.join(random.choice(chars) for _ in range(16))
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{timestamp}_{random_str}" 
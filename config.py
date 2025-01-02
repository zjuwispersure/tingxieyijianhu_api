import os
from datetime import timedelta
from urllib.parse import quote_plus

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    
    # 对密码进行 URL 编码
    password = quote_plus('sql@2024')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://yuwen:{password}@mysql:3306/yuwen'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    
    # 微信配置
    WECHAT_APP_ID = os.getenv('WECHAT_APP_ID')
    WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET')
    
    # 微信小程序配置
    WX_APP_ID = os.environ.get('WX_APP_ID')
    WX_APP_SECRET = os.environ.get('WX_APP_SECRET') 
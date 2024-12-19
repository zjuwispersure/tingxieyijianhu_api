import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 
        'mysql+pymysql://user:password@db:3306/dictation')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    
    # 微信配置
    WECHAT_APP_ID = os.getenv('WECHAT_APP_ID')
    WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET') 
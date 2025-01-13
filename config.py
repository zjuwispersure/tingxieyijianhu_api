import os
from datetime import timedelta

class Config:
    """基础配置类"""
    
    # 基本配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    TESTING = False
    DEBUG = True
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24小时
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=90)
    JWT_ERROR_MESSAGE_KEY = 'message'
    
    # 微信小程序配置
    WX_APP_ID = 'wx3e6bb70a5abcc7e6'
    WX_APP_SECRET = 'a2299eb5bbb13f5752ea51397d561acf'
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_FILE = 'app.log'
    
    # 听写配置
    DEFAULT_WORDS_PER_DICTATION = 10
    DEFAULT_REVIEW_DAYS = 3
    DEFAULT_DICTATION_INTERVAL = 5
    DEFAULT_DICTATION_RATIO = 100
    
    # API配置
    API_KEY = os.getenv('API_KEY', 'dev-api-key')
    API_RATE_LIMIT = '100/minute'
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav'}
    
    # Redis配置
    REDIS_URL = 'redis://redis:6379/0'
    CACHE_TIMEOUT = 300  # 缓存超时时间(秒)
    
    # 缓存键前缀
    CACHE_KEY_PREFIX = {
        'stats': 'stats',
        'task': 'task',
        'session': 'session',
        'word': 'word'
    }
    
    PRINT_ROUTES = os.getenv('PRINT_ROUTES', 'False').lower() == 'true'

class DevelopmentConfig(Config):
    """开发环境配置"""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'
    

class TestingConfig(Config):
    """测试环境配置"""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    

class ProductionConfig(Config):
    """生产环境配置"""
    
    # 生产环境必须设置的配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    WX_APP_ID = os.getenv('WX_APP_ID')
    WX_APP_SECRET = os.getenv('WX_APP_SECRET')
    
    # 生产环境特定配置
    LOG_LEVEL = 'WARNING'
    SQLALCHEMY_ECHO = False
    
    def __init__(self):
        # 验证必要的环境变量
        required_env_vars = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'WX_APP_ID',
            'WX_APP_SECRET',
            'DATABASE_URL'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f'Missing required environment variables: {", ".join(missing_vars)}'
            )

# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """获取当前环境的配置"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default']) 
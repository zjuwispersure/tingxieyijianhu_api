import os
from datetime import timedelta
from dotenv import load_dotenv
import logging

# 加载 .env 文件
load_dotenv()

class Config:
    """基础配置类"""
    
    # 基本配置
    DEBUG = True
    TESTING = False
    
    # 数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_MAX_OVERFLOW = 20
    
    # 事务超时设置（秒）
    SQLALCHEMY_POOL_PRE_PING = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'isolation_level': 'READ COMMITTED'  # 使用较低的隔离级别
    }
    
    # JWT配置
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)  # 设置较长的过期时间
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=90)
    JWT_ERROR_MESSAGE_KEY = 'message'
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  # 确保环境变量中有这个值
    
    # 日志配置
    ENABLE_SQL_LOG = False   # 新增：控制 SQL 日志的开关
    LOG_LEVEL = 'INFO'      # 新增：日志级别控制
    
    # 数据库连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # 连接池大小
        'pool_timeout': 30,  # 连接超时时间
        'pool_recycle': 3600,  # 连接回收时间(1小时)
        'pool_pre_ping': True,  # 每次请求前ping一下数据库，确保连接有效
        'max_overflow': 20,  # 最大溢出连接数
    }
    
    # MySQL配置
    MYSQL_TIMEOUT = 28800  # 8小时
    MYSQL_CHARSET = 'utf8mb4'
    
    @classmethod
    def init_app(cls, app):
        # 验证必需的环境变量
        required_env_vars = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'WX_APP_ID',
            'WX_APP_SECRET',
            'SQLALCHEMY_DATABASE_URI'
        ]
        
        for var in required_env_vars:
            if not app.config.get(var):
                raise ValueError(f'Missing required environment variable: {var}')
        
        # 配置 SQLAlchemy 日志
        if not app.config.get('ENABLE_SQL_LOG'):
            # 关闭 SQLAlchemy 日志
            logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
            logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
            logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
            logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)

class DevelopmentConfig(Config):
    """开发环境配置"""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True
    ENABLE_SQL_LOG = True  # 开发环境可以开启 SQL 日志
    LOG_LEVEL = 'DEBUG'
    

class TestingConfig(Config):
    """测试环境配置"""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    

class ProductionConfig(Config):
    """生产环境配置"""
    
    # 生产环境特定配置
    DEBUG = False
    ENABLE_SQL_LOG = False  # 生产环境关闭 SQL 日志
    LOG_LEVEL = 'WARNING'
    SQLALCHEMY_ECHO = False
    
    @classmethod
    def init_app(cls, app):
        # 先调用父类的初始化
        super().init_app(app)
        
        # 生产环境的额外检查
        if app.config.get('DEBUG'):
            raise ValueError('Production environment cannot run in debug mode')

# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(env_name=None):
    """获取当前环境的配置"""
    if env_name:
        return config.get(env_name, config['default'])
    return config[os.getenv('FLASK_ENV', 'default')]

# 导出配置类
__all__ = ['Config', 'get_config'] 
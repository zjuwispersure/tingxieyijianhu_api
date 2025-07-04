from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config, get_config
from .extensions import db, init_extensions
from .api import init_api
from .utils.cache import cache
from .utils.json_encoder import CustomJSONEncoder
import logging
import os
from sqlalchemy.exc import OperationalError
import time
import sys

logger = logging.getLogger(__name__)

def create_app(config_name=None):
    app = Flask(__name__)
    
    # 1. 首先加载环境变量中的配置
    for key, value in os.environ.items():
        if key.startswith('FLASK_'):
            app.config[key.replace('FLASK_', '')] = value
    
    # 2. 加载 .env 文件中的配置
    if os.path.exists('.env'):
        from dotenv import dotenv_values
        config_dict = dotenv_values('.env')
        app.config.update(config_dict)
    
    # 3. 加载基础配置类
    if config_name:
        config_class = get_config(config_name)
    else:
        config_class = get_config()
    
    app.config.from_object(config_class)
    
    # 4. 验证必需的配置
    required_configs = [
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'WX_APP_ID',
        'WX_APP_SECRET',
        'SQLALCHEMY_DATABASE_URI'
    ]
    
    missing_configs = [config for config in required_configs if not app.config.get(config)]
    if missing_configs:
        logger.error(f"Missing required configurations: {missing_configs}")
        raise RuntimeError(f"Missing required configurations: {missing_configs}")
    
    # 记录非敏感的配置信息
    logger.info(f"Environment: {app.config.get('ENV', 'production')}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    if app.config.get('WX_APP_ID'):
        logger.info(f"Using APP_ID: {app.config['WX_APP_ID'][:6]}...")
    
    # 配置日志级别
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    logging.getLogger('app').setLevel(log_level)
    
    if not app.config.get('ENABLE_SQL_LOG'):
        # 关闭 SQLAlchemy 日志
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    # 初始化扩展
    init_extensions(app)
    
    # 初始化其他扩展
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    cache.init_app(app)
    
    # 初始化 API 蓝图
    init_api(app)
    
    # 根据配置决定是否打印路由信息
    if app.config.get('PRINT_ROUTES'):
        print("\nRegistered routes:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    
    # JWT 错误处理
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'status': 'error',
            'code': 2001,
            'message': '请先登录'
        }), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({
            'status': 'error',
            'code': 2001,
            'message': '请先登录'
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({
            'status': 'error',
            'code': 2001,
            'message': 'token已过期，请重新登录'
        }), 401
    
    # 确保所有模型被导入，便于 Flask-Migrate 检测
    from app import models
    
    # 只在不是 Flask CLI 命令时才初始化数据库，防止迁移死循环
    if not (len(sys.argv) > 1 and sys.argv[1] in ['db', 'migrate', 'upgrade', 'downgrade', 'init']):
        try:
            init_extensions(app)
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    @app.before_request
    def before_request():
        """处理请求前的数据库会话检查"""
        max_retries = 3  # 最大重试次数
        retry_delay = 0.1  # 重试延迟（秒）
        
        for attempt in range(max_retries):
            try:
                if db.session.is_active:
                    # 如果有活跃事务，先尝试等待
                    if attempt < max_retries - 1:
                        logger.info(f"Active transaction found, waiting... (attempt {attempt + 1})")
                        time.sleep(retry_delay)
                        continue
                        
                    # 最后一次尝试，如果还有活跃事务，回滚并创建新会话
                    logger.warning("Forcing transaction cleanup after retries")
                    db.session.rollback()
                    db.session.remove()
                    db.session.begin()
                
                # 验证数据库连接
                db.session.execute('SELECT 1')
                break
                
            except OperationalError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Database connection failed after {max_retries} attempts")
                    # 这里不向外暴露具体错误，而是在内部处理
                    db.session.remove()
                    raise
                time.sleep(retry_delay)
                
    @app.teardown_request
    def cleanup_session(exception=None):
        """请求结束时清理会话"""
        if exception:
            logger.warning(f"Request ended with exception: {str(exception)}, rolling back...")
            db.session.rollback()
        db.session.remove()
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """应用上下文结束时清理会话"""
        if exception:
            logger.warning(f"Application context ended with exception: {str(exception)}")
            db.session.rollback()
        db.session.remove()
    
    @app.before_request
    def check_db_connection():
        """检查数据库连接状态"""
        try:
            db.session.execute('SELECT 1')
        except Exception:
            db.session.remove()
    
    app.json_encoder = CustomJSONEncoder
    
    return app

# 导出需要的内容
__all__ = ['create_app', 'db']

# 导入数据库实例
from .extensions import db  # noqa 
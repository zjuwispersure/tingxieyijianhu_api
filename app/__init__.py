from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config
from .models.database import db
from .api import init_api
from .utils.cache import cache

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # 确保配置在最开始就加载
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    
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
    
    return app

# 导出需要的内容
__all__ = ['create_app', 'db']

# 导入数据库实例
from .models.database import db  # noqa 
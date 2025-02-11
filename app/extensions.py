from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def init_extensions(app):
    # 配置 SQLAlchemy
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 3600,  # 一小时后回收连接
        'pool_pre_ping': True, # 在使用连接前先测试连接是否有效
        'pool_size': 10,       # 连接池大小
        'max_overflow': 20     # 超出 pool_size 后最多可以创建的连接数
    }
    
    db.init_app(app)
    migrate.init_app(app, db) 
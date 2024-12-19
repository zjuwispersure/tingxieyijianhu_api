from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

from config import Config
from .extensions import db, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)
    
    # 注册蓝图
    from .api import auth_bp, user_bp, family_bp, dictation_bp
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(family_bp, url_prefix='/api')
    app.register_blueprint(dictation_bp, url_prefix='/api')
    
    return app 
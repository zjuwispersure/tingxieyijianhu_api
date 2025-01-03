from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from .models.database import db

migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # 注册蓝图
    from .api import auth_bp, user_bp, family_bp, dictation_bp
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(family_bp, url_prefix='/api')
    app.register_blueprint(dictation_bp, url_prefix='/api')
    
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'ok'})
    
    return app 
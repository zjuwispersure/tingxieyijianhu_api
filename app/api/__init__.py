from flask import Blueprint
from .auth import auth_bp
from .family import family_bp
from .dictation import dictation_bp
from .health import health_bp

def init_api(app):
    """初始化所有 API 蓝图"""
    # 注册所有蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(dictation_bp)
    app.register_blueprint(health_bp)


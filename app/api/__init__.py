from flask import Blueprint
from .auth import auth_bp
from .user import user_bp
from .family import family_bp
from .textbook import textbook_bp
from .dictation import dictation_bp
from .review import review_bp
from .stats import stats_bp
from .analysis import analysis_bp
from .achievement import achievement_bp
from .ranking import ranking_bp
from .notification import notification_bp
from .admin import admin_bp
from .upload import upload_bp

api_bp = Blueprint('api', __name__)

# 注册所有蓝图
def init_app(app):
    """初始化所有API蓝图
    
    Args:
        app: Flask应用实例
    """
    blueprints = [
        auth_bp,
        user_bp,
        family_bp,
        textbook_bp,
        dictation_bp,
        review_bp,
        stats_bp,
        analysis_bp,
        achievement_bp,
        ranking_bp,
        notification_bp,
        admin_bp,
        upload_bp
    ]
    
    for bp in blueprints:
        app.register_blueprint(bp)

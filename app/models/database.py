from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """初始化数据库"""
    with app.app_context():
        # 验证所有模型
        db.create_all()
        
        # 测试查询
        from .user import User
        try:
            User.query.first()
            if app.config.get('ENABLE_SQL_LOG'):  # 只在开启日志时输出
                app.logger.info("Database initialization successful")
        except Exception as e:
            app.logger.error(f"Database initialization failed: {str(e)}")
            raise 
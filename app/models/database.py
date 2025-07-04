from app.extensions import db

# 保留 init_db 作为占位（如有需要可重构为工具函数），否则可删除整个文件。

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
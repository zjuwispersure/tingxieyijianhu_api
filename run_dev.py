import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # 确保 instance 目录存在
        import os
        if not os.path.exists('instance'):
            os.makedirs('instance')
        
        # 初始化数据库迁移
        from flask_migrate import init, migrate, upgrade
        init()
        migrate(message="Initial migration")
        upgrade()
        
        # 初始化数据库
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
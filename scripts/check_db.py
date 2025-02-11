from app import create_app, db
from app.models import User, Family, Child, DictationSession
from sqlalchemy import inspect

def check_database():
    """检查数据库表是否正确创建"""
    app = create_app()
    with app.app_context():
        try:
            # 检查各个表
            tables = [
                User.__table__,
                Family.__table__,
                Child.__table__,
                DictationSession.__table__,
                # ... 其他表
            ]
            
            inspector = inspect(db.engine)
            
            for table in tables:
                if not inspector.has_table(table.name):
                    print(f"Table {table.name} does not exist!")
                else:
                    print(f"Table {table.name} exists.")
                    
        except Exception as e:
            print(f"Error checking database: {str(e)}")
            raise

if __name__ == '__main__':
    check_database() 
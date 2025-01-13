from flask import Blueprint, jsonify, current_app
from ..models.database import db
import time
from sqlalchemy.exc import OperationalError

health_bp = Blueprint('health', __name__)

def try_connect_db(max_retries=5, retry_delay=2):
    """尝试连接数据库，带重试机制"""
    for i in range(max_retries):
        try:
            db.session.execute('SELECT 1')
            db.session.commit()
            return True
        except OperationalError as e:
            if i < max_retries - 1:  # 如果不是最后一次尝试
                current_app.logger.warning(f"Database connection attempt {i+1} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                raise e
    return False

@health_bp.route('/health')
def health_check():
    try:
        # 测试数据库连接
        try_connect_db()
        return jsonify({
            'status': 'ok',
            'database': 'connected'
        })
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'database': 'disconnected',
            'error': str(e)
        }), 500 
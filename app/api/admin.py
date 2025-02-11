from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timedelta

from app.utils.decorators import admin_required, log_api_call
from ..models import User, Child, DictationSession, YuwenItem, DictationDetail
from ..extensions import db
from ..utils.logger import logger
from ..utils.error_codes import *
import traceback
from sqlalchemy.exc import SQLAlchemyError

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users/list', methods=['GET'])
@jwt_required()
@admin_required
@log_api_call
def get_users():
    """获取用户列表
    
    请求参数:
    - page: 选填，页码（默认1）
    - per_page: 选填，每页数量（默认20）
    - keyword: 选填，搜索关键词
    
    返回数据:
    {
        "status": "success",
        "data": {
            "users": [{
                "id": 1,
                "nickname": "张三",
                "created_at": "2024-01-07T12:00:00Z",
                "children_count": 2,
                "last_active": "2024-01-07T12:00:00Z"
            }],
            "total": 100,
            "page": 1,
            "pages": 5
        }
    }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        
        # 构建查询
        query = User.query
        
        if keyword:
            query = query.filter(User.nickname.ilike(f'%{keyword}%'))
            
        # 分页
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page,
            per_page=per_page
        )
        
        # 获取用户信息
        result = []
        for user in pagination.items:
            children_count = Child.query.filter_by(user_id=user.id).count()
            last_session = DictationSession.query.join(
                Child
            ).filter(
                Child.user_id == user.id
            ).order_by(
                DictationSession.created_at.desc()
            ).first()
            
            result.append({
                'id': user.id,
                'nickname': user.nickname,
                'created_at': user.created_at.isoformat(),
                'children_count': children_count,
                'last_active': last_session.created_at.isoformat() if last_session else None
            })
            
        return jsonify({
            'status': 'success',
            'data': {
                'users': result,
                'total': pagination.total,
                'page': page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@admin_bp.route('/admin/textbook/import', methods=['POST'])
@jwt_required()
@admin_required
@log_api_call
def import_textbook():
    """导入教材数据
    
    请求参数:
    {
        "grade": 1,
        "semester": 1,
        "textbook_version": "rj",
        "items": [{
            "word": "你好",
            "pinyin": "nǐ hǎo",
            "unit": 1,
            "type": "识字"
        }]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'code': INVALID_REQUEST_FORMAT,
                'message': get_error_message(INVALID_REQUEST_FORMAT)
            }), 400
            
        # 验证必要字段
        required_fields = ['grade', 'semester', 'textbook_version', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'code': MISSING_REQUIRED_PARAM,
                    'message': get_error_message(MISSING_REQUIRED_PARAM, field)
                }), 400
                
        # 导入数据
        items = []
        for item_data in data['items']:
            item = YuwenItem(
                grade=data['grade'],
                semester=data['semester'],
                textbook_version=data['textbook_version'],
                word=item_data['word'],
                pinyin=item_data['pinyin'],
                unit=item_data['unit'],
                type=item_data['type']
            )
            items.append(item)
            
        try:
            db.session.bulk_save_objects(items)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"数据库错误: {str(e)}")
            return jsonify({
                'status': 'error',
                'code': DATABASE_ERROR,
                'message': get_error_message(DATABASE_ERROR)
            }), 500
            
        return jsonify({
            'status': 'success',
            'message': f'成功导入 {len(items)} 条数据'
        })
        
    except Exception as e:
        logger.error(f"导入教材数据失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@admin_bp.route('/admin/stats/overview', methods=['GET'])
@jwt_required()
@admin_required
@log_api_call
def get_admin_stats():
    """获取管理统计概览
    
    返回数据:
    {
        "status": "success",
        "data": {
            "total_users": 100,
            "total_children": 150,
            "total_tasks": 1000,
            "total_words": 5000,
            "daily_stats": [{
                "date": "2024-01-07",
                "new_users": 10,
                "active_users": 50,
                "tasks": 100,
                "words": 500
            }]
        }
    }
    """
    try:
        # 获取总体统计
        total_users = User.query.count()
        total_children = Child.query.count()
        total_tasks = DictationSession.query.count()
        total_words = YuwenItem.query.count()
        
        # 获取每日统计
        daily_stats = []
        for i in range(7):
            date = datetime.now().date() - timedelta(days=i)
            
            new_users = User.query.filter(
                func.date(User.created_at) == date
            ).count()
            
            active_users = DictationSession.query.filter(
                func.date(DictationSession.created_at) == date
            ).with_entities(
                func.count(func.distinct(DictationSession.child_id))
            ).scalar()
            
            tasks = DictationSession.query.filter(
                func.date(DictationSession.created_at) == date
            ).count()
            
            words = DictationDetail.query.join(
                DictationSession
            ).filter(
                func.date(DictationSession.created_at) == date
            ).count()
            
            daily_stats.append({
                'date': date.isoformat(),
                'new_users': new_users,
                'active_users': active_users,
                'tasks': tasks,
                'words': words
            })
            
        return jsonify({
            'status': 'success',
            'data': {
                'total_users': total_users,
                'total_children': total_children,
                'total_tasks': total_tasks,
                'total_words': total_words,
                'daily_stats': daily_stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取管理统计失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
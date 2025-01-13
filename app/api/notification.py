from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Notification
from ..extensions import db
from ..utils.logger import log_api_call, logger
from ..utils.error_codes import *
import traceback
from datetime import datetime

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/notifications/list', methods=['GET'])
@jwt_required()
@log_api_call
def get_notifications():
    """获取通知列表
    
    请求参数:
    - page: 选填，页码（默认1）
    - per_page: 选填，每页数量（默认20）
    - unread_only: 选填，是否只看未读（默认false）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "notifications": [{
                "id": 1,
                "type": "achievement",
                "title": "解锁新成就",
                "content": "恭喜解锁「初学乍练」成就！",
                "is_read": false,
                "created_at": "2024-01-07T12:00:00Z"
            }],
            "total": 100,
            "unread": 5,
            "page": 1,
            "pages": 5
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', type=bool)
        
        # 构建查询
        query = Notification.query.filter_by(
            user_id=int(user_id)
        )
        query = Notification.query.filter_by(
            user_id=int(user_id)
        )
        if unread_only:
            query = query.filter_by(is_read=False)
            
        # 分页
        pagination = query.order_by(
            Notification.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page
        )
        user_id=int(user_id),
        # 获取未读数量
        unread_count = Notification.query.filter_by(
            user_id=int(user_id),
            is_read=False
        ).count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'notifications': [n.to_dict() for n in pagination.items],
                'total': pagination.total,
                'unread': unread_count,
                'page': page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"获取通知列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@notification_bp.route('/notifications/read', methods=['POST'])
@jwt_required()
@log_api_call
def mark_as_read():
    """标记通知为已读
    
    请求参数:
    {
        "notification_ids": [1, 2, 3]  # 通知ID列表，为空则标记所有为已读
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
            
        notification_ids = data.get('notification_ids', [])
        
        user_id = int(get_jwt_identity())
        # 构建更新查询
        query = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        )
        
        if notification_ids:
            query = query.filter(Notification.id.in_(notification_ids))
            
        # 更新为已读
        query.update({'is_read': True})
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '标记成功'
        })
        
    except Exception as e:
        logger.error(f"标记通知已读失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
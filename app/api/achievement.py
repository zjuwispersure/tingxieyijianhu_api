from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required,get_jwt_identity
from ..models import Child, Achievement, UserAchievement
from ..extensions import db
from ..utils.logger import log_api_call, logger
from ..utils.error_codes import *
import traceback

achievement_bp = Blueprint('achievement', __name__)

@achievement_bp.route('/achievement/list', methods=['GET'])
@jwt_required()
@log_api_call
def get_achievements():
    """获取成就列表
    
    请求参数:
    - child_id: 必填，孩子ID
    
    返回数据:
    {
        "status": "success", 
        "data": {
            "achievements": [{
                "id": 1,
                "name": "初学乍练",
                "description": "完成第一次听写",
                "icon": "http://...",
                "unlocked": true,
                "unlock_time": "2024-01-07T12:00:00Z",
                "progress": 100,
                "target": 100
            }]
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400

        user_id = get_jwt_identity() 
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=child_id,
            user_id=int(user_id)
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        # 获取所有成就
        achievements = Achievement.query.all()
        
        # 获取已解锁的成就
        unlocked = UserAchievement.query.filter_by(
            child_id=child_id
        ).all()
        unlocked_ids = {ua.achievement_id for ua in unlocked}
        
        # 计算成就进度
        result = []
        for achievement in achievements:
            progress = achievement.calculate_progress(child_id)
            unlocked = achievement.id in unlocked_ids
            unlock_time = next(
                (ua.unlock_time for ua in unlocked if ua.achievement_id == achievement.id),
                None
            )
            
            result.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'unlocked': unlocked,
                'unlock_time': unlock_time.isoformat() if unlock_time else None,
                'progress': progress,
                'target': achievement.target
            })
            
        return jsonify({
            'status': 'success',
            'data': {
                'achievements': result
            }
        })
        
    except Exception as e:
        logger.error(f"获取成就列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
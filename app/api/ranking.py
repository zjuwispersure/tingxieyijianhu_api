from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.utils.decorators import log_api_call
from ..models import Child, DictationSession, DictationDetail, YuwenItem
from ..extensions import db
from ..utils.logger import logger
from ..utils.error_codes import *
import traceback
from sqlalchemy import func, Integer
from datetime import datetime, timedelta

ranking_bp = Blueprint('ranking', __name__)

@ranking_bp.route('/ranking/daily', methods=['GET'])
@jwt_required()
@log_api_call
def get_daily_ranking():
    """获取每日排行榜
    
    请求参数:
    - child_id: 必填，孩子ID
    - date: 选填，日期(YYYY-MM-DD)，默认今天
    
    返回数据:
    {
        "status": "success",
        "data": {
            "ranking": [{
                "rank": 1,
                "child_id": 1,
                "nickname": "小明",
                "words": 100,
                "accuracy": 0.95,
                "is_self": true
            }],
            "self_rank": 1,
            "total_users": 100
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        date_str = request.args.get('date')
        
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400
            
        # 验证孩子所有权
        user_id = get_jwt_identity()
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
            
        # 解析日期
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        except ValueError:
            return jsonify({
                'status': 'error',
                'code': INVALID_PARAM_VALUE,
                'message': get_error_message(INVALID_PARAM_VALUE, 'date')
            }), 400
            
        # 获取排行榜数据
        ranking_data = db.session.query(
            Child.id,
            Child.nickname,
            func.count(DictationDetail.id).label('words'),
            func.sum(DictationDetail.is_correct.cast(Integer)).label('correct')
        ).join(
            DictationSession
        ).join(
            DictationDetail
        ).filter(
            func.date(DictationSession.created_at) == date
        ).group_by(
            Child.id
        ).order_by(
            func.sum(DictationDetail.is_correct.cast(Integer)).desc(),
            func.count(DictationDetail.id).desc()
        ).all()
        
        # 格式化数据
        result = []
        self_rank = None
        for rank, data in enumerate(ranking_data, 1):
            is_self = data.id == child_id
            if is_self:
                self_rank = rank
                
            result.append({
                'rank': rank,
                'child_id': data.id,
                'nickname': data.nickname,
                'words': data.words,
                'accuracy': data.correct / data.words if data.words else 0,
                'is_self': is_self
            })
            
        return jsonify({
            'status': 'success',
            'data': {
                'ranking': result,
                'self_rank': self_rank,
                'total_users': len(ranking_data)
            }
        })
        
    except Exception as e:
        logger.error(f"获取每日排行榜失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 

@ranking_bp.route('/ranking/family', methods=['GET'])
@jwt_required()
@log_api_call
def get_family_ranking():
    """获取家庭成员排名
    
    请求参数:
    - family_id: 必填，家庭ID
    - start_date: 必填，开始日期(YYYY-MM-DD)
    
    返回数据:
    {
        "status": "success",
        "data": {
            "ranking": [{
                "rank": 1,
                "child_id": 1,
                "nickname": "小明",
                "words": 100,
                "accuracy": 0.95,
                "is_self": true
            }],
            "self_rank": 1,
            "total_users": 100
        }
    }
    """
    try:
        family_id = request.args.get('family_id', type=int)
        start_date_str = request.args.get('start_date')
        
        if not family_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'family_id')
            }), 400
            
        # 验证家庭成员所有权
        user_id = get_jwt_identity()
        child = Child.query.filter_by(
            id=family_id,
            user_id=int(user_id)
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        # 解析日期
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else datetime.now().date()
        except ValueError:
            return jsonify({
                'status': 'error',
                'code': INVALID_PARAM_VALUE,
                'message': get_error_message(INVALID_PARAM_VALUE, 'start_date')
            }), 400
            
        # 获取家庭成员排名
        rankings = DictationDetail.query.join(
            DictationSession, Child
        ).filter(
            Child.family_id == family_id,
            DictationSession.created_at >= start_date
        ).group_by(
            Child.id
        ).with_entities(
            Child.id,
            Child.nickname,
            func.count(DictationDetail.id).label('total_words'),
            func.sum(DictationDetail.is_correct.cast(Integer)).label('correct_words')
        ).order_by(
            func.sum(DictationDetail.is_correct.cast(Integer)).desc()
        ).all()
        
        # 格式化数据
        result = []
        self_rank = None
        for rank, data in enumerate(rankings, 1):
            is_self = data.id == family_id
            if is_self:
                self_rank = rank
                
            result.append({
                'rank': rank,
                'child_id': data.id,
                'nickname': data.nickname,
                'words': data.total_words,
                'accuracy': data.correct_words / data.total_words if data.total_words else 0,
                'is_self': is_self
            })
            
        return jsonify({
            'status': 'success',
            'data': {
                'ranking': result,
                'self_rank': self_rank,
                'total_users': len(rankings)
            }
        })
        
    except Exception as e:
        logger.error(f"获取家庭成员排名失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required
from ..models import Child, DictationTask, DictationTaskItem, DictationSession
from ..extensions import db
from ..utils.logger import log_api_call, logger
from ..utils.error_codes import *
import traceback
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

task_bp = Blueprint('task', __name__)

@task_bp.route('/api/task/list', methods=['GET'])
@jwt_required()
@log_api_call
def get_task_list():
    """获取听写任务列表
    
    请求参数:
    - child_id: 必填，孩子ID
    - page: 选填，页码（默认1）
    - per_page: 选填，每页数量（默认20）
    
    返回数据:
    {
        "status": "success",
        "data": {
            "tasks": [{
                "id": 1,
                "created_at": "2024-01-07T12:00:00Z",
                "total_words": 10,
                "correct_words": 8,
                "accuracy_rate": 0.8,
                "status": "completed"
            }],
            "total": 100,
            "page": 1,
            "pages": 5
        }
    }
    """
    try:
        child_id = request.args.get('child_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400
            
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=child_id,
            user_id=g.user.id
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        # 获取任务列表
        pagination = DictationTask.query.filter_by(
            child_id=child_id
        ).order_by(
            DictationTask.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'tasks': [task.to_dict() for task in pagination.items],
                'total': pagination.total,
                'page': page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@task_bp.route('/api/task/<int:task_id>/detail', methods=['GET'])
@jwt_required()
@log_api_call
def get_task_detail(task_id):
    """获取听写任务详情
    
    返回数据:
    {
        "status": "success",
        "data": {
            "task": {
                "id": 1,
                "created_at": "2024-01-07T12:00:00Z",
                "status": "completed",
                "items": [{
                    "word": "你好",
                    "pinyin": "nǐ hǎo",
                    "is_correct": true,
                    "user_input": "你好"
                }]
            }
        }
    }
    """
    try:
        # 验证任务所有权
        task = DictationTask.query.filter_by(
            id=task_id,
            user_id=g.user.id
        ).first()
        
        if not task:
            return jsonify({
                'status': 'error',
                'code': RESOURCE_NOT_FOUND,
                'message': get_error_message(RESOURCE_NOT_FOUND)
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'task': task.to_dict(with_items=True)
            }
        })
        
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@task_bp.route('/api/task/<int:task_id>/submit', methods=['POST'])
@jwt_required()
@log_api_call
def submit_task(task_id):
    """提交听写结果
    
    请求参数:
    {
        "items": [{
            "id": 1,
            "word": "你好",
            "user_input": "你好"
        }]
    }
    """
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'items')
            }), 400
            
        # 验证任务所有权
        task = DictationTask.query.filter_by(
            id=task_id,
            user_id=g.user.id
        ).first()
        
        if not task:
            return jsonify({
                'status': 'error',
                'code': RESOURCE_NOT_FOUND,
                'message': get_error_message(RESOURCE_NOT_FOUND)
            }), 404
            
        # 更新任务项
        for item_data in data['items']:
            item = DictationTaskItem.query.filter_by(
                id=item_data['id'],
                task_id=task_id
            ).first()
            
            if item:
                item.user_input = item_data['user_input']
                item.is_correct = item.word == item_data['user_input']
                
        # 更新任务状态
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        
        try:
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
            'data': {
                'task': task.to_dict(with_items=True)
            }
        })
        
    except Exception as e:
        logger.error(f"提交听写结果失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@task_bp.route('/api/task/session/start', methods=['POST'])
@jwt_required()
@log_api_call
def start_session():
    """开始听写会话
    
    请求参数:
    {
        "child_id": 1,
        "task_id": 1
    }
    
    返回数据:
    {
        "status": "success",
        "data": {
            "session": {
                "id": 1,
                "task_id": 1,
                "start_time": "2024-01-07T12:00:00Z",
                "status": "in_progress"
            }
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'child_id' not in data or 'task_id' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id 和 task_id')
            }), 400
            
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=data['child_id'],
            user_id=g.user.id
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        # 验证任务所有权
        task = DictationTask.query.filter_by(
            id=data['task_id'],
            child_id=child.id
        ).first()
        
        if not task:
            return jsonify({
                'status': 'error',
                'code': RESOURCE_NOT_FOUND,
                'message': get_error_message(RESOURCE_NOT_FOUND)
            }), 404
            
        # 检查是否有未完成的会话
        active_session = DictationSession.query.filter_by(
            task_id=task.id,
            status='in_progress'
        ).first()
        
        if active_session:
            return jsonify({
                'status': 'error',
                'code': SESSION_ALREADY_EXISTS,
                'message': get_error_message(SESSION_ALREADY_EXISTS)
            }), 400
            
        # 创建新会话
        session = DictationSession(
            task=task,
            start_time=datetime.utcnow(),
            status='in_progress'
        )
        
        try:
            db.session.add(session)
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
            'data': {
                'session': session.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"开始听写会话失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@task_bp.route('/api/task/session/<int:session_id>/submit', methods=['POST'])
@jwt_required()
@log_api_call
def submit_session():
    """提交听写结果
    
    请求参数:
    {
        "items": [{
            "item_id": 1,
            "word": "你好",
            "user_input": "你好",
            "time_spent": 10  # 秒数
        }]
    }
    
    返回数据:
    {
        "status": "success",
        "data": {
            "session": {
                "id": 1,
                "task_id": 1,
                "start_time": "2024-01-07T12:00:00Z",
                "end_time": "2024-01-07T12:10:00Z",
                "status": "completed",
                "items": [{
                    "word": "你好",
                    "is_correct": true,
                    "user_input": "你好",
                    "time_spent": 10
                }]
            }
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'items')
            }), 400
            
        # 验证会话
        session = DictationSession.query.get(session_id)
        if not session:
            return jsonify({
                'status': 'error',
                'code': RESOURCE_NOT_FOUND,
                'message': get_error_message(RESOURCE_NOT_FOUND)
            }), 404
            
        # 验证任务所有权
        task = session.task
        if task.child.user_id != g.user.id:
            return jsonify({
                'status': 'error',
                'code': PERMISSION_DENIED,
                'message': get_error_message(PERMISSION_DENIED)
            }), 403
            
        # 验证会话状态
        if session.status != 'in_progress':
            return jsonify({
                'status': 'error',
                'code': INVALID_SESSION_STATUS,
                'message': get_error_message(INVALID_SESSION_STATUS)
            }), 400
            
        # 更新任务项
        for item_data in data['items']:
            item = DictationTaskItem.query.filter_by(
                id=item_data['item_id'],
                task_id=task.id
            ).first()
            
            if item:
                item.user_input = item_data['user_input']
                item.is_correct = item.word == item_data['user_input']
                item.time_spent = item_data['time_spent']
                item.review_count += 1
                
        # 更新会话状态
        session.status = 'completed'
        session.end_time = datetime.utcnow()
        
        try:
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
            'data': {
                'session': session.to_dict(with_items=True)
            }
        })
        
    except Exception as e:
        logger.error(f"提交听写结果失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
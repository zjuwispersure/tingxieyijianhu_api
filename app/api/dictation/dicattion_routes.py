from datetime import datetime
from flask import jsonify, request, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.child import Child
from app.models.dictation_session import DictationSession, DictationDetail
from app.models.dictation_task import DictationSession, DictationTask, DictationTaskItem
from . import dictation_bp
from ...models.yuwen_item import YuwenItem
from ...models.family import DictationRecord, FamilyMember
from ...models.dictation_config import DictationConfig
from ...extensions import db
from ...utils.logger import logger
from ...utils.decorators import log_api_call, require_family_access
from ...utils.error_codes import *
import traceback

#### yuwen数据相关的路由
@dictation_bp.route('/yuwen/lessons')
@jwt_required()
@log_api_call
def get_all_lessons():
    """获取所有课次信息"""
    try:
        # 获取必需参数
        grade = request.args.get('grade', type=int)
        semester = request.args.get('semester', type=int)
        version = request.args.get('version')
        
        # 参数验证
        if not all([grade, semester, version]):
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': '缺少必需参数'
            }), 400
            
        lessons = YuwenItem.get_all_lessons(
            grade=grade,
            semester=semester,
            textbook_version=version
        )
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': lessons
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_all_lessons: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500

@dictation_bp.route('/yuwen/lesson/items')
@jwt_required()
@log_api_call
def get_lesson_items():
    """获取课次的词语列表"""
    try:
        # 获取必需参数
        grade = request.args.get('grade', type=int)
        semester = request.args.get('semester', type=int)
        version = request.args.get('version')
        lesson = request.args.get('lesson', type=int)
        
        # 参数验证
        if not all([grade, semester, version, lesson]):
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': '缺少必需参数'
            }), 400
            
        items = YuwenItem.get_items_by_lesson_id(
            grade=grade,
            semester=semester,
            textbook_version=version,
            lesson=lesson
        )
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': [item.to_dict() for item in items]
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_lesson_items: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500

@dictation_bp.route('/yuwen/unit/items')
@jwt_required()
@log_api_call
def get_unit_items():
    """获取单元的词语列表"""
    try:
        # 获取必需参数
        grade = request.args.get('grade', type=int)
        semester = request.args.get('semester', type=int)
        version = request.args.get('version')
        unit = request.args.get('unit', type=int)
        
        # 参数验证
        if not all([grade, semester, version, unit]):
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': '缺少必需参数'
            }), 400
            
        items = YuwenItem.get_items_by_unit(
            grade=grade,
            semester=semester,
            textbook_version=version,
            unit=unit
        )
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': [item.to_dict() for item in items]
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_unit_items: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500

### record相关的路由
@dictation_bp.route('/dictation/record', methods=['POST'])
@jwt_required()
@log_api_call
@require_family_access
def create_dictation_record():
    """创建听写记录"""
    try:
        # 开启事务
        db.session.begin_nested()
        
        data = request.get_json()
        child_id = data.get('child_id')
        yuwen_item_id = data.get('yuwen_item_id')
        score = data.get('score')
        
        # 使用 g.family_id
        family_id = g.family_id
        
        try:
            # 验证child是否属于该家庭
            child = FamilyMember.query.filter_by(
                id=child_id,
                family_id=family_id,
                is_child=True
            ).first()
            
            if not child:
                return jsonify({
                    'status': 'error',
                    'code': 400,
                    'message': '无效的child_id'
                }), 400
                
            record = DictationRecord(
                family_id=family_id,
                child_id=child_id,
                recorder_id=get_jwt_identity(),
                yuwen_item_id=yuwen_item_id,
                score=score
            )
            
            db.session.add(record)
            db.session.flush()
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'code': 0,
                'data': record.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"Error in create_dictation_record: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500

@dictation_bp.route('/dictation/records/<int:family_id>')
@jwt_required()
@log_api_call
@require_family_access
def get_family_records(family_id: int):
    """获取家庭的听写记录"""
    try:
        child_id = request.args.get('child_id', type=int)
        
        query = DictationRecord.query.filter_by(family_id=family_id)
        if child_id:
            query = query.filter_by(child_id=child_id)
            
        records = query.order_by(DictationRecord.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': [record.to_dict() for record in records]
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_family_records: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500


#### config相关的路由
@dictation_bp.route('/dictation/config/update', methods=['POST'])
@jwt_required()
@log_api_call
def update_dictation_config():
    """更新听写配置"""
    try:
        # 开启事务
        db.session.begin_nested()
        
        data = request.get_json()
        child_id = data.get('child_id')
        
        try:
            # 验证 child_id 是否存在
            child = Child.query.get(child_id)
            if not child:
                return jsonify({
                    'status': 'error',
                    'code': 400,
                    'message': '无效的child_id'
                }), 400
                
            config = DictationConfig.query.filter_by(child_id=child_id).first()
            if not config:
                config = DictationConfig(child_id=child_id)
                
            config.words_per_dictation = data.get('words_per_dictation', 10)
            config.review_days = data.get('review_days', 3)
            config.dictation_interval = data.get('dictation_interval', 5)
            config.dictation_ratio = data.get('dictation_ratio', 100)
            
            db.session.add(config)
            db.session.flush()
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': '配置更新成功'
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"更新听写配置失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@dictation_bp.route('/dictation/config/get', methods=['GET'])
@jwt_required()
@log_api_call
def get_config():
    """获取听写配置"""
    try:
        child_id = request.args.get('child_id', type=int)
        if not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM, 'child_id')
            }), 400
            
        # 验证孩子所有权
        child = Child.query.filter_by(
            id=child_id,
            user_id=int(get_jwt_identity())
        ).first()
        
        if not child:
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': get_error_message(CHILD_NOT_FOUND)
            }), 404
            
        # 获取配置
        config = DictationConfig.query.filter_by(child_id=child_id).first()
        if not config:
            config = DictationConfig(child_id=child_id)
            db.session.add(config)
            db.session.commit()
            
        return jsonify({
            'status': 'success',
            'data': {
                'config': config.to_dict()
            }
        })
        
    except Exception as e:
        logger.error(f"获取听写配置失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@dictation_bp.route('/dictation/task/create', methods=['POST'])
@jwt_required()
@log_api_call
def create_dictation_task():
    """创建听写任务"""
    try:
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        
        try:
            # 验证必要参数
            if not all(k in data for k in ['child_id', 'words']):
                return jsonify({
                    'status': 'error',
                    'code': MISSING_REQUIRED_PARAM,
                    'message': get_error_message(MISSING_REQUIRED_PARAM)
                }), 400
            
            # 创建任务
            task = DictationTask(
                child_id=data['child_id'],
                subject='yuwen',
                source='unit',
                words_count=len(data['words'])
            )
            db.session.add(task)
            db.session.flush()
            
            # 创建任务项
            for word_data in data['words']:
                task_item = DictationTaskItem(
                    task_id=task.id,
                    yuwen_item_id=word_data['id'],
                    word=word_data['word']
                )
                db.session.add(task_item)
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {'task_id': task.id}
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"创建听写任务失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@dictation_bp.route('/dictation/submit', methods=['POST'])
@jwt_required()
@log_api_call
def submit_dictation_result():
    """提交听写结果"""
    try:
        # 开启事务
        db.session.begin_nested()
        data = request.get_json()
        
        try:
            # 验证必要参数
            if not all(k in data for k in ['task_id', 'results']):
                return jsonify({
                    'status': 'error',
                    'code': MISSING_REQUIRED_PARAM,
                    'message': get_error_message(MISSING_REQUIRED_PARAM)
                }), 400
            
            # 创建听写会话
            session = DictationSession(
                task_id=data['task_id'],
                total_words=len(data['results'])
            )
            db.session.add(session)
            db.session.flush()
            
            # 记录每个词的结果
            for result in data['results']:
                detail = DictationDetail(
                    session_id=session.id,
                    task_item_id=result['item_id'],
                    user_input=result['input'],
                    is_correct=result['is_correct'],
                    time_spent=result.get('time_spent'),
                    retry_count=result.get('retry_count', 0)
                )
                db.session.add(detail)
                if result['is_correct']:
                    session.correct_count += 1
            
            # 更新会话状态
            session.status = 'completed'
            session.end_time = datetime.utcnow()
            session.calculate_stats()
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {'session_id': session.id}
            })
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"提交听写结果失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500
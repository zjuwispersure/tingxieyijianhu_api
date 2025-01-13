from flask import jsonify, request, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import dictation_bp
from ...models.yuwen_item import YuwenItem
from ...models.family import DictationRecord, FamilyMember
from ...models.dictation_config import DictationConfig
from ...extensions import db
from ...utils.logger import logger
from ...utils.decorators import log_api_call, require_family_access
from ...utils.error_codes import *
import traceback

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

@dictation_bp.route('/dictation/record', methods=['POST'])
@jwt_required()
@log_api_call
@require_family_access
def create_dictation_record():
    """创建听写记录"""
    try:
        data = request.get_json()
        child_id = data.get('child_id')
        yuwen_item_id = data.get('yuwen_item_id')
        score = data.get('score')
        
        # 使用 g.family_id
        family_id = g.family_id
        
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
        
        record.save()
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'data': record.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error in create_dictation_record: {str(e)}", exc_info=True)
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

@dictation_bp.route('/dictation/config/update', methods=['POST'])
@jwt_required()
@log_api_call
def update_dictation_config():
    """更新听写配置"""
    try:
        data = request.get_json()
        child_id = data.get('child_id')
        
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
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '配置更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新听写配置失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500 
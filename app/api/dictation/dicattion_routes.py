from datetime import datetime
from flask import jsonify, request, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.child import Child
from app.models.dictation import DictationDetail, DictationSession, DictationConfig
from . import dictation_bp
from ...models.yuwen_item import YuwenItem
from ...models.family import DictationRecord, FamilyMember
from ...extensions import db
from ...utils.logger import logger
from ...utils.decorators import log_api_call, require_family_access, with_db_retry
from ...utils.error_codes import (
    MISSING_REQUIRED_PARAM, 
    INVALID_PARAMETER, 
    INTERNAL_ERROR,
    SESSION_NOT_FOUND
)
import traceback
from sqlalchemy.exc import IntegrityError

#### yuwen数据相关的路由
@dictation_bp.route('/yuwen/lessons/all')
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
            lesson=lesson,
            type='词语'
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
    """获取指定单元的所有生字词条目
    
    获取指定教材版本、年级、学期和单元的所有生字词条目，包括字、词、句等。
    
    Query Parameters:
        grade (int): 年级 (1-6)
        semester (int): 学期 (1-2)
        unit (int): 单元号 (1-8)
        version (str): 教材版本，可选值：
            - rj: 人教版
            - bsd: 北师大版
            - sj: 苏教版
        
    Returns:
        成功返回:
        {
            'status': 'success',
            'code': 0,
            'data': {
                'items': [
                    {
                        'id': int,          # 条目ID
                        'type': str,        # 条目类型(word/phrase/sentence)
                        'content': str,     # 内容
                        'pinyin': str,      # 拼音
                        'unit': int,        # 单元号
                        'lesson': int,      # 课次
                        'grade': int,       # 年级
                        'semester': int,    # 学期
                        'textbook_version': str  # 教材版本
                    },
                    ...
                ]
            }
        }
        
        失败返回:
        {
            'status': 'error',
            'code': MISSING_REQUIRED_PARAM,  # 缺少必需参数
            'message': '缺少必需参数: {param_name}'
        }
        
    Raises:
        400: 缺少必需参数或参数无效
        500: 服务器内部错误
    """
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
@with_db_retry()
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

@dictation_bp.route('/dictation/submit', methods=['POST'])
@jwt_required()
@log_api_call
def submit_dictation_result():
    """提交听写结果
    
    请求体:
    {
        "session_id": 456,
        "config": {
            "time_spent": 300,
            "end_time": "2025-01-17T11:35:00Z"
        },
        "results": [
            {
                "yuwen_item_id": 123,
                "word": "奇观",
                "is_correct": true
            }
        ]
    }
    """
    try:
        data = request.get_json()
        session_id = int(data['session_id'])
        current_app.logger.info(f"Looking for session: {session_id}")
        
        session = DictationSession.query.get(session_id)
        current_app.logger.info(f"Found session: {session}")
        
        if not session:
            return jsonify({
                'status': 'error',
                'code': SESSION_NOT_FOUND,
                'message': '听写会话不存在'
            }), 404
            
        # 更新会话信息
        session.status = 'completed'
        session.end_time = datetime.now()
        session.total_time = (session.end_time - session.start_time).seconds  # 计算总用时
        
        # 更新每个词的结果
        correct_count = 0
        for result in data['results']:
            detail = DictationDetail.query.filter_by(
                session_id=session.id,
                yuwen_item_id=result['item_id']
            ).first()
            
            if detail:
                detail.is_correct = result['is_correct']
                detail.user_input = result.get('user_input')
                detail.retry_count = result.get('retry_count', 0)
                detail.time_spent = result.get('time_spent', 0)  # 记录该词用时
                
                if not detail.is_correct:
                    detail.error_count += 1
                    detail.last_wrong_time = datetime.now()
                else:
                    correct_count += 1
        
        # 更新统计信息
        session.correct_words = correct_count
        session.total_words = len(data['results'])
        session.accuracy = correct_count / session.total_words if session.total_words > 0 else 0
        session.score = session.accuracy * 100  # 转换为百分制分数
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': session.to_dict()
        })
            
    except Exception as e:
        logger.error(f"提交听写结果失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@dictation_bp.route('/dictation/start', methods=['POST'])
@jwt_required()
@log_api_call
def start_dictation():
    """开始听写任务
    
    请求体:
    {
        "child_id": 123,
        "name": "第一单元听写",  # 可选
        "items": [
            123,  # yuwen_item_id 列表
            124,
            125
        ],
        "config": {  # 本次听写的配置
            "dictation_interval": 5,    # 听写间隔(秒)
            "retry_limit": 3,           # 重听次数限制
            "auto_play": true,          # 是否自动播放
            "wrong_words_only": false,  # 是否只听写错词
            "random_order": false       # 是否随机顺序
        }
    }
    """
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        child_id = data.get('child_id')
        
        # 验证 child_id 是否存在
        child = Child.query.get(child_id)
        if not child:
            has_children = Child.query.filter_by(user_id=current_user_id).first() is not None
            message = '请先添加孩子信息' if not has_children else '找不到指定的孩子记录'
            return jsonify({
                'status': 'error',
                'code': CHILD_NOT_FOUND,
                'message': message
            }), 404
            
        # 验证必要参数
        if not all(k in data for k in ['items']):
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': get_error_message(MISSING_REQUIRED_PARAM)
            }), 400
            
        # 批量查询词语信息
        yuwen_items = YuwenItem.query.filter(
            YuwenItem.id.in_(data['items'])
        ).all()
        
        # 创建词语ID到对象的映射
        yuwen_item_map = {item.id: item for item in yuwen_items}
        
        # 检查是否所有请求的词语都存在
        missing_ids = set(data['items']) - set(yuwen_item_map.keys())
        if missing_ids:
            return jsonify({
                'status': 'error',
                'code': INVALID_PARAMETER,
                'message': f'词语不存在: {missing_ids}'
            }), 400
            
        # 创建听写会话
        session = DictationSession(
            child_id=child_id,
            session_type='practice',
            status='in_progress',
            start_time=datetime.utcnow(),
            total_words=len(data['items'])
        )
        db.session.add(session)
        db.session.flush()
        
        current_app.logger.info(f"Created new dictation session: {session.id}")
        
        # 获取或更新孩子的听写配置
        if 'config' in data:
            config = DictationConfig(
                session_id=session.id,
                child_id=child_id,
                dictation_interval=data['config'].get('dictation_interval', 5),
                retry_limit=data['config'].get('retry_limit', 3),
                auto_play=data['config'].get('auto_play', True),
                wrong_words_only=data['config'].get('wrong_words_only', False),
                random_order=data['config'].get('random_order', False),
                dictation_mode=data['config'].get('dictation_mode', 'unit')
            )
            db.session.add(config)
        
        # 创建听写详情记录
        for item_id in data['items']:
            item = yuwen_item_map[item_id]
            detail = DictationDetail(
                session_id=session.id,
                yuwen_item_id=item.id,
                word=item.word,
                is_correct=None,
                user_input=None
            )
            db.session.add(detail)
            
        try:
            db.session.commit()
            current_app.logger.info(f"Successfully created dictation session {session.id} with {len(data['items'])} items")
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"创建听写会话失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'code': INTERNAL_ERROR,
                'message': '创建听写会话失败'
            }), 500
            
        return jsonify({
            'status': 'success',
            'data': {
                'session_id': session.id
            }
        })
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"开始听写失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': INTERNAL_ERROR,
            'message': get_error_message(INTERNAL_ERROR)
        }), 500

@dictation_bp.route('/dictation/stats/daily', methods=['GET'])
@jwt_required()
def get_daily_stats():
    try:
        today = datetime.now().date()
        current_app.logger.info(f"Getting daily stats for date: {today}")
        stats = DictationSession.get_daily_stats(today)
        current_app.logger.info(f"Daily stats: {stats}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'total': stats['total'],      # 今日听写总数
                'correct': stats['correct'],  # 今日正确数
                'accuracy': stats['accuracy'] # 正确率
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_daily_stats: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500

@dictation_bp.route('/dictation/stats/unit', methods=['GET'])
@jwt_required()
def get_unit_stats():
    """获取单元错题统计
    
    Query Parameters:
        unit (int): 单元号
        lesson (int, optional): 课次号
        child_id (int): 孩子ID
        
    Returns:
        {
            'status': 'success',
            'data': {
                'words': [{
                    'id': int,
                    'word': str,
                    'error_count': int,
                    'total_count': int,
                    'last_wrong_time': str
                }]
            }
        }
    """
    try:
        unit = request.args.get('unit', type=int)
        lesson = request.args.get('lesson', type=int)
        child_id = request.args.get('child_id', type=int)
        
        if not unit or not child_id:
            return jsonify({
                'status': 'error',
                'code': MISSING_REQUIRED_PARAM,
                'message': '缺少必要参数'
            }), 400
            
        stats = DictationSession.get_unit_stats(
            unit=unit,
            lesson=lesson,
            child_id=child_id
        )
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_unit_stats: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500

@dictation_bp.route('/dictation/stats/overall', methods=['GET'])
@jwt_required()
def get_overall_stats():
    try:
        stats = DictationSession.get_overall_stats()
        current_app.logger.info(f"Overall stats: {stats}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'total': stats['total'],           # 累计听写总数
                'correct': stats['correct'],       # 累计正确数
                'accuracy': stats['accuracy'],     # 总正确率
                'week_count': stats['week_count'], # 本周数量
                'month_count': stats['month_count'], # 本月数量
                'avg_score': stats['avg_score'],   # 平均分
                'best_score': stats['best_score']  # 最高分
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_overall_stats: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e)
        }), 500
from flask import Blueprint, jsonify, request, g
from datetime import datetime
import random
from ..models import (
    DictationTask,
    DictationTaskItem, 
    DictationSession
)
from ..models.database import db
from ..utils.logger import log_message
from ..utils.auth import login_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import YuwenItem
from sqlalchemy import func
from sqlalchemy import Integer

dictation_bp = Blueprint('dictation', __name__)

@dictation_bp.route('/api/dictation/yuwen/items', methods=['GET'])
@login_required
def get_yuwen_items():
    """获取语文学习项（字/词）列表"""
    grade = request.args.get('grade', type=int)
    semester = request.args.get('semester', type=int)
    unit = request.args.get('unit', type=int)
    item_type = request.args.get('type')  # 识字/写字/词语
    book_version = request.args.get('book_version', 'renjiaoban')
    
    query = YuwenItem.query
    
    if grade:
        query = query.filter_by(grade=grade)
    if semester:
        query = query.filter_by(semester=semester)
    if unit:
        query = query.filter_by(unit=unit)
    if item_type:
        query = query.filter_by(type=item_type)
    if book_version:
        query = query.filter_by(book_version=book_version)
        
    items = query.all()
    
    return jsonify({
        'code': 0,
        'data': [{
            'id': item.id,
            'word': item.word,
            'pinyin': item.pinyin,
            'hint': item.hint,
            'type': item.type,
            'unit': item.unit,
            'audio_path': item.audio_path
        } for item in items]
    })

@dictation_bp.route('/api/dictation/yuwen/by_unit', methods=['POST'])
@login_required
def yuwen_unit_dictation():
    """语文按单元听写"""
    data = request.get_json()
    child_id = data['child_id']
    unit = data['unit']
    config = data.get('config', {})
    
    # 获取孩子的教材配置
    textbook_config = get_user_textbook_config(child_id)
    
    # 获取听写内容
    items = get_dictation_by_unit(
        grade=textbook_config['grade'],
        semester=textbook_config['semester'],
        unit=unit,
        book_version=textbook_config['book_version'],
        item_type=data.get('item_type', '识字')
    )
    
    task = create_dictation_task(
        user_id=g.user.id,
        child_id=child_id,
        words=items,
        subject='yuwen',
        source='unit',
        config=config
    )
    
    return jsonify({
        'code': 0,
        'data': task.to_dict()
    })

@dictation_bp.route('/api/dictation/yuwen/smart', methods=['POST'])
@login_required
def yuwen_smart_dictation():
    """语文智能听写"""
    data = request.get_json()
    child_id = data['child_id']
    config = data.get('config', {})
    
    # 获取需要复习的词语
    words = get_review_words(
        child_id=child_id,
        subject='yuwen',
        limit=config.get('words_per_dictation', 10)
    )
    
    task = create_dictation_task(
        user_id=g.user.id,
        child_id=child_id,
        words=words,
        subject='yuwen',
        source='smart',
        config=config
    )
    
    return jsonify({
        'code': 0,
        'data': task.to_dict()
    })

def get_review_words(child_id, subject, item_type='识字', limit=10):
    """获取需要复习的内容
    Args:
        child_id: 孩子ID
        subject: 学科
        item_type: 类型（识字/写字/词语）
        limit: 返回数量
    """
    # 获取孩子的教材配置
    config = get_user_textbook_config(child_id)
    
    # 获取已完成的听写任务项
    completed_items = DictationTaskItem.query.join(
        DictationTask
    ).filter(
        DictationTask.child_id == child_id,
        DictationTask.subject == subject
    ).join(
        YuwenItem
    ).filter(
        YuwenItem.type == item_type,
        YuwenItem.book_version == config['book_version'],
        YuwenItem.grade == config['grade'],
        YuwenItem.semester == config['semester']
    ).with_entities(
        YuwenItem,
        func.avg(DictationTaskItem.is_correct).label('accuracy')
    ).group_by(
        YuwenItem.id
    ).having(
        func.avg(DictationTaskItem.is_correct) < 0.8  # 正确率低于80%需要复习
    ).all()
    
    if not completed_items:
        return []
    
    # 按正确率排序（正确率低的优先复习）
    items = sorted(completed_items, key=lambda x: x.accuracy or 0)
    selected_items = items[:limit]
    
    return [{
        'id': item.YuwenItem.id,
        'word': item.YuwenItem.word,
        'pinyin': item.YuwenItem.pinyin,
        'hint': item.YuwenItem.hint,
        'audio_path': item.YuwenItem.audio_path
    } for item in selected_items]

def create_dictation_task(user_id, child_id, words, subject, source, config=None):
    """创建听写任务"""
    task = DictationTask(
        user_id=user_id,
        child_id=child_id,
        subject=subject,
        source=source,
        words_count=len(words)
    )
    db.session.add(task)
    db.session.flush()  # 获取 task.id
    
    # 保存任务词语
    for word_data in words:
        item = DictationTaskItem(
            task_id=task.id,
            yuwen_item_id=word_data['id']  # 使用 YuwenItem 的 ID
        )
        db.session.add(item)
    
    db.session.commit()
    return task

@dictation_bp.route('/api/dictation/statistics', methods=['GET'])
@login_required
def get_dictation_statistics():
    """获取听写统计信息"""
    task_id = request.args.get('task_id', type=int)
    child_id = request.args.get('child_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 构建查询
    query = DictationSession.query
    
    if task_id:
        query = query.filter_by(task_id=task_id)
    if child_id:
        query = query.join(DictationTask).filter(DictationTask.child_id == child_id)
    if start_date:
        query = query.filter(DictationSession.start_time >= start_date)
    if end_date:
        query = query.filter(DictationSession.end_time <= end_date)
        
    sessions = query.all()
    
    # 计算统计数据
    total_words = sum(session.total_words for session in sessions)
    correct_words = sum(session.correct_count for session in sessions)
    
    return jsonify({
        'total_sessions': len(sessions),
        'total_words': total_words,
        'correct_words': correct_words,
        'accuracy_rate': correct_words / total_words if total_words > 0 else 0,
        'sessions': [session.to_dict() for session in sessions]
    })

@dictation_bp.route('/api/dictation/progress/<int:child_id>')
@login_required
def get_learning_progress(child_id):
    """获取学习进度"""
    # 获取孩子的教材配置
    config = get_user_textbook_config(child_id)
    
    # 获取听写任务项的统计数据
    unit_stats = {}
    
    # 查询所有听写任务项
    task_items = DictationTaskItem.query.join(
        DictationTask
    ).filter(
        DictationTask.child_id == child_id
    ).join(
        YuwenItem
    ).filter(
        YuwenItem.book_version == config['book_version'],
        YuwenItem.grade == config['grade'],
        YuwenItem.semester == config['semester']
    ).with_entities(
        YuwenItem.unit,
        func.count(DictationTaskItem.id).label('total'),
        func.sum(DictationTaskItem.is_correct.cast(Integer)).label('correct_count')
    ).group_by(
        YuwenItem.unit
    ).all()
    
    # 格式化单元统计
    by_unit = [{
        'unit': item.unit,
        'total': item.total,
        'learned': item.total,  # 已经听写过的就是学习过的
        'mastered': item.correct_count,
        'accuracy_rate': item.correct_count / item.total if item.total > 0 else 0
    } for item in task_items]
    
    # 计算总体统计
    total_words = sum(item.total for item in task_items)
    correct_words = sum(item.correct_count for item in task_items)
    
    return jsonify({
        'total_words': total_words,
        'learned_words': total_words,
        'mastered_words': correct_words,
        'accuracy_rate': correct_words / total_words if total_words > 0 else 0,
        'by_unit': by_unit
    })

def get_dictation_by_unit(grade, semester, unit, book_version='renjiaoban', item_type='识字', count=10):
    """根据单元获取听写内容"""
    items = YuwenItem.query.filter_by(
        grade=grade,
        semester=semester,
        unit=unit,
        book_version=book_version,
        type=item_type
    ).limit(count).all()
    
    return [{
        'id': item.id,  # 添加 ID
        'word': item.word,
        'pinyin': item.pinyin,
        'hint': item.hint,
        'audio_path': item.audio_path
    } for item in items]

def get_smart_dictation(grade, semester, child_id, book_version='renjiaoban', item_type='识字', count=10):
    """智能获取听写内容（基于学习进度和掌握程度）
    Args:
        grade: 年级
        semester: 学期
        child_id: 孩子ID
        book_version: 教材版本（如：renjiaoban）
        item_type: 类型（识字/写字/词语）
        count: 返回数量
    """
    # 获取当前单元
    current_unit = get_current_unit(grade, semester)
    
    # 70% 当前单元的内容
    current_items = YuwenItem.query.filter_by(
        grade=grade,
        semester=semester,
        unit=current_unit,
        book_version=book_version,
        type=item_type
    ).order_by(func.random()).limit(int(count * 0.7)).all()
    
    # 30% 之前单元的复习内容
    review_items = YuwenItem.query.filter(
        YuwenItem.grade == grade,
        YuwenItem.semester == semester,
        YuwenItem.unit < current_unit,
        YuwenItem.book_version == book_version,
        YuwenItem.type == item_type
    ).order_by(func.random()).limit(count - len(current_items)).all()
    
    items = current_items + review_items
    random.shuffle(items)
    
    return [{
        'word': item.word,
        'pinyin': item.pinyin,
        'hint': item.hint,
        'audio_path': item.audio_path
    } for item in items]

def get_current_unit(grade, semester):
    """获取当前学习单元"""
    # 这里可以根据实际需求实现具体的逻辑
    # 比如从学习进度表中获取，或者根据日期计算等
    return 1 

def get_user_textbook_config(child_id, subject='yuwen'):
    """获取孩子的教材配置
    Args:
        child_id: 孩子ID
        subject: 学科（默认：yuwen）
    Returns:
        dict: {
            'book_version': 教材版本,
            'grade': 年级,
            'semester': 学期
        }
    """
    from app.models import Child, DictationConfig
    
    # 获取孩子信息
    child = Child.query.get(child_id)
    if not child:
        return {
            'book_version': 'renjiaoban',  # 默认人教版
            'grade': 1,
            'semester': 1
        }
    
    # 获取听写配置
    config = DictationConfig.query.filter_by(child_id=child_id).first()
    
    return {
        'book_version': config.book_version if config else 'renjiaoban',
        'grade': child.grade,
        'semester': child.semester
    } 
from flask import Blueprint, jsonify, request, g
from datetime import datetime
import random
from app.models import DictationTask, Word, WordLearningStatus
from app.utils.auth import login_required

bp = Blueprint('dictation', __name__)

@bp.route('/api/dictation/yuwen/by_unit', methods=['POST'])
@login_required
def yuwen_unit_dictation():
    """语文按单元听写"""
    data = request.get_json()
    child_id = data['child_id']
    unit = data['unit']
    grade = data['grade']
    semester = data['semester']
    config = data.get('config', {})
    
    # 获取单元词语
    words = Word.query.filter_by(
        grade=grade,
        semester=semester,
        unit=unit,
        subject='yuwen'  # 标记学科
    ).all()
    
    task = create_dictation_task(
        user_id=g.user.id,
        child_id=child_id,
        words=words,
        subject='yuwen',
        source='unit',
        config=config
    )
    
    return jsonify({
        'code': 0,
        'data': task.to_dict()
    })

@bp.route('/api/dictation/yuwen/smart', methods=['POST'])
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

def get_review_words(child_id, subject, limit=10):
    """获取需要复习的词语"""
    now = datetime.utcnow()
    
    # 获取所有需要复习的词语状态
    learning_status = WordLearningStatus.query.join(Word).filter(
        WordLearningStatus.child_id == child_id,
        WordLearningStatus.next_review_time <= now,
        Word.subject == subject
    ).all()
    
    # 计算选择权重
    word_weights = [
        (status.word, 1 - status.mastery_level)
        for status in learning_status
    ]
    
    # 加权随机选择
    if word_weights:
        words, weights = zip(*word_weights)
        return random.choices(words, weights=weights, k=min(limit, len(words)))
    return []

def create_dictation_task(user_id, child_id, words, subject, source, config=None):
    """创建听写任务"""
    task = DictationTask(
        user_id=user_id,
        child_id=child_id,
        subject=subject,
        source=source,
        words_count=len(words),
        **config if config else {}
    )
    
    # 保存任务词语
    task.add_words(words)
    db.session.add(task)
    db.session.commit()
    
    return task 

@bp.route('/api/dictation/statistics', methods=['GET'])
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

@bp.route('/api/dictation/progress/<int:child_id>')
@login_required
def get_learning_progress(child_id):
    """获取学习进度"""
    # 获取所有学习状态
    learning_status = WordLearningStatus.query.filter_by(child_id=child_id).all()
    
    # 按单元统计
    unit_stats = {}
    for status in learning_status:
        unit = status.word.unit
        if unit not in unit_stats:
            unit_stats[unit] = {
                'total': 0,
                'learned': 0,
                'mastered': 0,
                'correct_count': 0
            }
        
        stats = unit_stats[unit]
        stats['total'] += 1
        if status.first_learn_time:
            stats['learned'] += 1
        if status.mastery_level >= 0.8:  # 掌握度达到80%认为已掌握
            stats['mastered'] += 1
        stats['correct_count'] += status.correct_count
    
    # 格式化单元统计
    by_unit = [
        {
            'unit': unit,
            'total': stats['total'],
            'learned': stats['learned'],
            'mastered': stats['mastered'],
            'accuracy_rate': stats['correct_count'] / (stats['learned'] * stats['total']) if stats['learned'] > 0 else 0
        }
        for unit, stats in unit_stats.items()
    ]
    
    # 计算总体统计
    total_words = sum(stats['total'] for stats in unit_stats.values())
    learned_words = sum(stats['learned'] for stats in unit_stats.values())
    mastered_words = sum(stats['mastered'] for stats in unit_stats.values())
    need_review = sum(
        1 for status in learning_status 
        if status.first_learn_time and status.next_review_time <= datetime.utcnow()
    )
    
    return jsonify({
        'total_words': total_words,
        'learned_words': learned_words,
        'mastered_words': mastered_words,
        'need_review': need_review,
        'by_unit': by_unit
    }) 
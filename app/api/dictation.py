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
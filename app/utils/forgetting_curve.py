from datetime import datetime, timedelta
from ..models.dictation import Dictation

def calculate_review_words(child_id, word_count):
    """
    根据遗忘曲线算法计算需要复习的单词
    
    遗忘曲线复习时间点：
    1. 第1次复习：5分钟后
    2. 第2次复习：30分钟后
    3. 第3次复习：12小时后
    4. 第4次复习：1天后
    5. 第5次复习：2天后
    6. 第6次复习：4天后
    7. 第7次复习：7天后
    8. 第8次复习：15天后
    """
    
    # 获取该学生的所有听写记录
    dictations = Dictation.query.filter_by(child_id=child_id).all()
    
    # 统计每个单词的错误次数和上次复习时间
    word_stats = {}
    for d in dictations:
        for word, result in zip(d.content, d.result):
            if word not in word_stats:
                word_stats[word] = {
                    'error_count': 0,
                    'last_review': d.created_at,
                    'review_count': 1
                }
            else:
                word_stats[word]['review_count'] += 1
                word_stats[word]['last_review'] = d.created_at
                
            if not result['is_correct']:
                word_stats[word]['error_count'] += 1
    
    # 计算每个单词的复习优先级
    now = datetime.utcnow()
    word_priority = []
    
    for word, stats in word_stats.items():
        time_diff = now - stats['last_review']
        review_interval = get_review_interval(stats['review_count'])
        
        if time_diff >= review_interval:
            priority = calculate_priority(
                stats['error_count'],
                time_diff,
                review_interval
            )
            word_priority.append((word, priority))
    
    # 按优先级排序并返回需要复习的单词
    word_priority.sort(key=lambda x: x[1], reverse=True)
    return [word for word, _ in word_priority[:word_count]]

def get_review_interval(review_count):
    """获取复习间隔时间"""
    intervals = [
        timedelta(minutes=5),
        timedelta(minutes=30),
        timedelta(hours=12),
        timedelta(days=1),
        timedelta(days=2),
        timedelta(days=4),
        timedelta(days=7),
        timedelta(days=15)
    ]
    
    if review_count <= len(intervals):
        return intervals[review_count - 1]
    return intervals[-1]

def calculate_priority(error_count, time_diff, review_interval):
    """计算��词复习优先级"""
    # 错误次数权重
    error_weight = error_count * 0.4
    
    # 时间差权重
    time_weight = (time_diff / review_interval).total_seconds() * 0.6
    
    return error_weight + time_weight 
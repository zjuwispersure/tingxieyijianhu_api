from datetime import datetime, timedelta
from .database import db
from .base import BaseModel
from sqlalchemy import func, case
from sqlalchemy.sql import extract
from .yuwen_item import YuwenItem

class DictationSession(BaseModel):
    """听写会话模型"""
    __tablename__ = 'dictation_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    session_type = db.Column(db.String(20), nullable=False)  # practice, test
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed
    current_word_index = db.Column(db.Integer, default=0)
    total_words = db.Column(db.Integer, default=0)
    correct_words = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    score = db.Column(db.Float, default=0.0)      # 分数(0-100)
    total_time = db.Column(db.Integer, default=0)  # 总用时(秒)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    answers = db.relationship('DictationAnswer', back_populates='session', lazy='dynamic')
    config = db.relationship('DictationConfig', back_populates='session', uselist=False)
    details = db.relationship('DictationDetail', back_populates='session', lazy='dynamic')
    child = db.relationship('Child', back_populates='dictation_sessions')

    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'session_type': self.session_type,
            'status': self.status,
            'current_word_index': self.current_word_index,
            'total_words': self.total_words,
            'correct_words': self.correct_words,
            'accuracy': self.accuracy,
            'score': self.score,
            'total_time': self.total_time,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def get_daily_stats(cls, date=None, child_id=None):
        """获取每日统计
        Args:
            date: 指定日期，默认今天
            child_id: 指定孩子ID
        """
        if date is None:
            date = datetime.now().date()
            
        query = cls.query.filter(
            func.date(cls.created_at) == date
        )
        
        if child_id:
            query = query.filter_by(child_id=child_id)
            
        result = query.with_entities(
            func.count(cls.id).label('total_sessions'),
            func.sum(cls.total_words).label('total_words'),
            func.sum(cls.correct_words).label('correct_words'),
            func.avg(cls.accuracy).label('accuracy')
        ).first()
        
        return {
            'total': int(float(result.total_words or 0)),
            'correct': int(float(result.correct_words or 0)),
            'accuracy': int(float(result.accuracy or 0) * 100)
        }

    @classmethod
    def get_overall_stats(cls, child_id=None):
        """获取整体统计
        Args:
            child_id: 指定孩子ID
        """
        query = cls.query
        if child_id:
            query = query.filter_by(child_id=child_id)
            
        # 基础统计
        base_stats = query.with_entities(
            func.sum(cls.total_words).label('total_words'),
            func.sum(cls.correct_words).label('correct_words'),
            func.avg(cls.accuracy).label('accuracy'),
            func.max(cls.accuracy).label('best_score')
        ).first()
        
        # 本周数量
        week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
        week_count = query.filter(
            func.date(cls.created_at) >= week_start
        ).with_entities(
            func.sum(cls.total_words)
        ).scalar() or 0
        
        # 本月数量
        month_count = query.filter(
            extract('month', cls.created_at) == datetime.now().month,
            extract('year', cls.created_at) == datetime.now().year
        ).with_entities(
            func.sum(cls.total_words)
        ).scalar() or 0
        
        return {
            'total': int(float(base_stats.total_words or 0)),
            'correct': int(float(base_stats.correct_words or 0)),
            'accuracy': int(float(base_stats.accuracy or 0) * 100),
            'week_count': int(float(week_count)),
            'month_count': int(float(month_count)),
            'avg_score': int(float(base_stats.accuracy or 0) * 100),
            'best_score': int(float(base_stats.best_score or 0) * 100)
        }

    @classmethod
    def get_unit_stats(cls, unit, lesson=None, child_id=None):
        """获取单元错题统计
        Args:
            unit: 单元号
            lesson: 课次号(可选)
            child_id: 孩子ID
        """
        from .dictation import DictationDetail
        
        # 构建基础查询
        query = db.session.query(
            YuwenItem.id,
            YuwenItem.word,
            func.count(DictationDetail.id).label('total_count'),
            func.sum(case([(DictationDetail.is_correct == False, 1)], else_=0)).label('error_count'),
            func.max(case([(DictationDetail.is_correct == False, DictationDetail.created_at)], else_=None)).label('last_wrong_time')
        ).join(
            DictationDetail, DictationDetail.yuwen_item_id == YuwenItem.id
        ).join(
            cls, DictationDetail.session_id == cls.id
        ).filter(
            YuwenItem.unit == unit
        )
        
        # 添加可选过滤条件
        if lesson:
            query = query.filter(YuwenItem.lesson == lesson)
        if child_id:
            query = query.filter(cls.child_id == child_id)
        
        # 分组并获取结果
        results = query.group_by(
            YuwenItem.id
        ).having(
            func.sum(case([(DictationDetail.is_correct == False, 1)], else_=0)) > 0  # 只返回有错误的词
        ).all()
        
        return {
            'words': [{
                'id': r.id,
                'word': r.word,
                'error_count': int(float(r.error_count or 0)),
                'total_count': int(float(r.total_count or 0)),
                'last_wrong_time': r.last_wrong_time.isoformat() if r.last_wrong_time else None
            } for r in results]
        }

class DictationAnswer(BaseModel):
    """听写答案模型"""
    __tablename__ = 'dictation_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('dictation_sessions.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('yuwen_items.id'), nullable=False)
    answer = db.Column(db.String(100))
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    session = db.relationship('DictationSession', back_populates='answers')
    word = db.relationship('YuwenItem') 

class DictationDetail(BaseModel):
    """听写详情模型"""
    __tablename__ = 'dictation_details'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('dictation_sessions.id'), nullable=False)
    yuwen_item_id = db.Column(db.Integer, db.ForeignKey('yuwen_items.id'), nullable=False)
    word = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    user_input = db.Column(db.String(100))
    retry_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    last_wrong_time = db.Column(db.DateTime)
    time_spent = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    session = db.relationship('DictationSession', back_populates='details')
    yuwen_item = db.relationship('YuwenItem')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'yuwen_item_id': self.yuwen_item_id,
            'word': self.word,
            'is_correct': self.is_correct,
            'user_input': self.user_input,
            'retry_count': self.retry_count,
            'error_count': self.error_count,
            'last_wrong_time': self.last_wrong_time.isoformat() if self.last_wrong_time else None,
            'time_spent': self.time_spent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def calculate_mastery_level(self):
        """计算掌握程度"""
        if self.attempts == 0:
            return 0.0
        return self.correct_count / self.attempts * 100

    def update_review_schedule(self):
        """更新复习计划"""
        if not self.last_practice_time:
            return

        # 基于艾宾浩斯遗忘曲线的复习间隔（单位：小时）
        review_intervals = [1, 24, 72, 168, 360, 720]
        
        if self.review_stage < len(review_intervals):
            hours = review_intervals[self.review_stage]
            self.next_review_time = self.last_practice_time + timedelta(hours=hours)
            self.review_stage += 1 

class DictationConfig(BaseModel):
    """听写配置"""
    __tablename__ = 'dictation_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('dictation_sessions.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    words_per_dictation = db.Column(db.Integer, default=10)  # 每次听写词数
    review_days = db.Column(db.Integer, default=3)           # 复习间隔天数
    dictation_interval = db.Column(db.Integer, default=5)    # 听写间隔秒数
    dictation_ratio = db.Column(db.Integer, default=100)     # 听写比例(百分比)
    dictation_mode = db.Column(db.String(20), default='unit')  # unit:单元听写, smart:智能听写
    retry_limit = db.Column(db.Integer, default=3)            # 重听次数限制
    auto_play = db.Column(db.Boolean, default=True)           # 是否自动播放
    wrong_words_only = db.Column(db.Boolean, default=False)   # 是否只听写错词
    random_order = db.Column(db.Boolean, default=False)       # 是否随机顺序

    # 关联关系
    session = db.relationship('DictationSession', back_populates='config', uselist=False)
    child = db.relationship('Child', back_populates='dictation_config')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'child_id': self.child_id,
            'words_per_dictation': self.words_per_dictation,
            'review_days': self.review_days,
            'dictation_interval': self.dictation_interval,
            'dictation_ratio': self.dictation_ratio,
            'dictation_mode': self.dictation_mode,
            'retry_limit': self.retry_limit,
            'auto_play': self.auto_play,
            'wrong_words_only': self.wrong_words_only,
            'random_order': self.random_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
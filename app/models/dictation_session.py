from datetime import datetime
from .base import BaseModel
from .database import db

class DictationSession(BaseModel):
    """听写会话"""
    __tablename__ = 'dictation_sessions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('dictation_tasks.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    total_words = db.Column(db.Integer, default=0)
    correct_count = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    
    # 统计信息
    accuracy_rate = db.Column(db.Float)
    time_spent = db.Column(db.Integer)  # 总用时(秒)
    
    # 关系
    task = db.relationship('app.models.dictation_task.DictationTask', back_populates='sessions')
    details = db.relationship('app.models.dictation_session.DictationDetail', back_populates='session', cascade='all, delete-orphan')

    def calculate_stats(self):
        """计算听写统计信息"""
        if self.details:
            self.total_words = len(self.details)
            self.correct_count = sum(1 for d in self.details if d.is_correct)
            self.accuracy_rate = self.correct_count / self.total_words if self.total_words > 0 else 0
            if self.end_time and self.start_time:
                self.time_spent = int((self.end_time - self.start_time).total_seconds())

class DictationDetail(BaseModel):
    """听写详情表 - 记录每个词的听写结果"""
    __tablename__ = 'dictation_details'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('dictation_sessions.id'), nullable=False)
    task_item_id = db.Column(db.Integer, db.ForeignKey('dictation_task_items.id'), nullable=False)
    
    # 听写结果
    user_input = db.Column(db.String(32))
    is_correct = db.Column(db.Boolean)
    time_spent = db.Column(db.Integer)  # 单词用时(秒)
    retry_count = db.Column(db.Integer, default=0)
    
    # 关系
    session = db.relationship('app.models.dictation_session.DictationSession', back_populates='details')
    task_item = db.relationship('app.models.dictation_task.DictationTaskItem', back_populates='details') 
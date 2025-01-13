from .base import BaseModel
from .database import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class DictationTask(BaseModel):
    """听写任务"""
    __tablename__ = 'dictation_tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    subject = Column(String(20), nullable=False)  # yuwen/english
    source = Column(String(20), nullable=False)   # unit/smart
    words_count = Column(Integer, nullable=False)
    
    # 关联的听写内容
    items = relationship("DictationTaskItem", back_populates="task")
    sessions = relationship("DictationSession", back_populates="task")
    child = relationship("Child", back_populates="dictation_tasks")

class DictationTaskItem(BaseModel):
    """听写任务内容项"""
    __tablename__ = 'dictation_task_items'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('dictation_tasks.id'), nullable=False)
    yuwen_item_id = Column(Integer, ForeignKey('yuwen_items.id'), nullable=False)
    is_correct = Column(Boolean, default=None)
    answer = Column(String(50))
    
    task = relationship("DictationTask", back_populates="items")
    yuwen_item = db.relationship('YuwenItem')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'yuwen_item_id': self.yuwen_item_id,
            'is_correct': self.is_correct,
            'answer': self.answer,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DictationSession(BaseModel):
    """听写会话记录"""
    __tablename__ = 'dictation_sessions'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('dictation_tasks.id'), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    total_words = Column(Integer, nullable=False)
    correct_count = Column(Integer, default=0)
    
    task = relationship("DictationTask", back_populates="sessions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_words': self.total_words,
            'correct_count': self.correct_count,
            'accuracy_rate': self.correct_count / self.total_words if self.total_words > 0 else 0
        } 
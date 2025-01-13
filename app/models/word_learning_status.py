from app.models.base import BaseModel
from .database import db
from datetime import datetime

class WordLearningStatus(BaseModel):
    """词语学习状态模型 - 存储学生的学习状态"""
    __tablename__ = 'word_learning_status'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    word = db.Column(db.String(50), nullable=False)  # 冗余存储,方便查询
    yuwen_item_id = db.Column(db.Integer, db.ForeignKey('yuwen_items.id'), nullable=False)
    
    # 学习状态
    learning_stage = db.Column(db.Integer, default=0)  # 学习阶段
    review_count = db.Column(db.Integer, default=0)  # 复习次数
    next_review = db.Column(db.DateTime)  # 下次复习时间
    is_mastered = db.Column(db.Boolean, default=False)  # 是否已掌握
    
    
    # 索引
    __table_args__ = (
        db.Index('idx_child_word', child_id, word),  # 联合索引,加速查询
    )
    
    def __repr__(self):
        return f'<WordLearningStatus {self.word}>'
        
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'child_id': self.child_id,
            'word': self.word,
            'yuwen_item_id': self.yuwen_item_id,
            'learning_stage': self.learning_stage,
            'review_count': self.review_count,
            'next_review': self.next_review.isoformat() if self.next_review else None,
            'is_mastered': self.is_mastered,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
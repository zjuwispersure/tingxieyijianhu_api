from datetime import datetime
from .base import BaseModel
from .database import db

class DictationConfig(BaseModel):
    """听写配置"""
    __tablename__ = 'dictation_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    words_per_dictation = db.Column(db.Integer, default=10)  # 每次听写词数
    review_days = db.Column(db.Integer, default=3)           # 复习间隔天数
    dictation_interval = db.Column(db.Integer, default=5)    # 听写间隔秒数
    dictation_ratio = db.Column(db.Integer, default=100)     # 听写比例(百分比)

    # 关联关系
    child = db.relationship('Child', back_populates='dictation_config', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'words_per_dictation': self.words_per_dictation,
            'review_days': self.review_days,
            'dictation_interval': self.dictation_interval,
            'dictation_ratio': self.dictation_ratio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
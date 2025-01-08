from .database import db
from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class DictationConfig(db.Model):
    """听写配置"""
    __tablename__ = 'dictation_configs'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    words_per_dictation = Column(Integer, default=10)  # 每次听写词数
    review_days = Column(Integer, default=3)           # 复习间隔天数
    dictation_interval = Column(Integer, default=5)    # 听写间隔秒数
    dictation_ratio = Column(Integer, default=100)     # 听写比例(百分比)
    wrong_words_only = Column(Boolean, default=False)  # 是否只听写错词
    
    # 关联关系
    child = relationship("Child", back_populates="dictation_config")
    
    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'words_per_dictation': self.words_per_dictation,
            'review_days': self.review_days,
            'dictation_interval': self.dictation_interval,
            'dictation_ratio': self.dictation_ratio,
            'wrong_words_only': self.wrong_words_only
        } 
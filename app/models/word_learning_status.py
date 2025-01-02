from datetime import datetime, timedelta
from .base import Base
from .database import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

class WordLearningStatus(Base):
    """词语学习状态表"""
    __tablename__ = 'word_learning_status'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    
    # 学习状态
    first_learn_time = Column(DateTime)         # 首次学习时间
    last_review_time = Column(DateTime)         # 最后复习时间
    next_review_time = Column(DateTime)         # 下次复习时间
    review_count = Column(Integer, default=0)   # 复习次数
    correct_count = Column(Integer, default=0)  # 正确次数
    mastery_level = Column(Float, default=0)    # 掌握程度(0-1)
    
    # 关联关系
    child = relationship("Child", back_populates="word_learning_status")
    word = relationship("Word", back_populates="learning_status")

    def update_after_dictation(self, is_correct):
        """听写后更新状态"""
        now = datetime.utcnow()
        if not self.first_learn_time:
            self.first_learn_time = now
            
        self.last_review_time = now
        self.review_count += 1
        if is_correct:
            self.correct_count += 1
            
        # 更新掌握程度
        self.mastery_level = self.correct_count / self.review_count
        
        # 根据艾宾浩斯遗忘曲线设置下次复习时间
        days_interval = self._calculate_next_review_interval()
        self.next_review_time = now + timedelta(days=days_interval)
    
    def _calculate_next_review_interval(self):
        """计算下次复习间隔天数"""
        if self.review_count == 1:
            return 1  # 第一次复习后1天
        elif self.review_count == 2:
            return 2  # 第二次复习后2天
        elif self.review_count == 3:
            return 4  # 第三次复习后4天
        elif self.review_count == 4:
            return 7  # 第四次复习后7天
        else:
            return 15  # 之后每次15天 
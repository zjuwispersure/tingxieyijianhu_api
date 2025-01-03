from .database import db
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey

class WordLearningStatus(db.Model):
    __tablename__ = 'word_learning_status'
    
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    
    # 学习状态
    first_learn_time = Column(DateTime)
    last_review_time = Column(DateTime)
    next_review_time = Column(DateTime)
    review_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    mastery_level = Column(Float, default=0) 
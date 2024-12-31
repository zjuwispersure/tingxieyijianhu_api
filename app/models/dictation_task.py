from datetime import datetime
from app.models.base import Base
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

class DictationTask(Base):
    """听写任务配置表"""
    __tablename__ = 'dictation_tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    child_id = Column(Integer, ForeignKey('children.id'), nullable=False)
    subject = Column(String(20), nullable=False)  # 学科：yuwen/english
    source = Column(String(20), nullable=False)   # 来源：unit/smart
    
    # 听写配置
    audio_play_count = Column(Integer, default=2)     # 音频播放次数
    audio_interval = Column(Integer, default=3)       # 音频播放间隔(秒)
    words_per_dictation = Column(Integer, default=10) # 每次听写词语数量
    words_count = Column(Integer)                 # 实际词语数量
    
    # 任务状态
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)           # 是否激活
    
    # 关联关系
    user = relationship("User", back_populates="dictation_tasks")
    child = relationship("Child", back_populates="dictation_tasks")
    sessions = relationship("DictationSession", back_populates="task") 
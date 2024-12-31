from app.models.base import Base
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

class DictationConfig(Base):
    """听写配置表"""
    __tablename__ = 'dictation_config'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # 音频播放配置
    audio_play_count = Column(Integer, default=2)     # 音频播放次数
    audio_interval = Column(Integer, default=3)       # 音频播放间隔(秒)
    
    # 听写内容配置
    words_per_dictation = Column(Integer, default=10) # 每次听写词语数量
    new_words_ratio = Column(Float, default=0.7)      # 新词比例
    review_words_ratio = Column(Float, default=0.3)   # 复习词比例
    
    # 难度配置
    error_retry_limit = Column(Integer, default=2)    # 错误重试次数
    pass_score = Column(Integer, default=80)          # 及格分数
    
    # 关联关系
    user = relationship("User", back_populates="dictation_config")

    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        for key, value in kwargs.items():
            setattr(self, key, value) 
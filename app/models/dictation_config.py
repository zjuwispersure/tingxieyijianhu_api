from .database import db
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

class DictationConfig(db.Model):
    """听写配置表"""
    __tablename__ = 'dictation_configs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    show_pinyin = Column(Boolean, default=False)
    show_radical = Column(Boolean, default=False)
    show_explanation = Column(Boolean, default=False)
    voice_type = Column(String(20), default='female')  # male/female
    voice_speed = Column(Integer, default=1)  # 1-3 
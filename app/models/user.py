from .database import db
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    openid = Column(String(50), unique=True, nullable=False)
    nickname = Column(String(50))
    avatar_url = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 使用字符串引用避免循环导入
    children = relationship("Child")
    dictation_config = relationship("DictationConfig") 
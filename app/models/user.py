from .database import db
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    openid = Column(String(50), unique=True, nullable=False)
    nickname = Column(String(50))
    avatar_url = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nickname': self.nickname,
            'openid': self.openid,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 
from datetime import datetime
from ..extensions import db
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(64), unique=True, nullable=False)
    nickname = db.Column(db.String(64))
    avatar = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    children = db.relationship('Child', backref='user', lazy=True)
    families = db.relationship('Family', backref='creator', lazy=True)
    dictation_config = relationship("DictationConfig", 
                                   back_populates="user", 
                                   uselist=False)  # one-to-one关系
    dictation_tasks = relationship("DictationTask", back_populates="user")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nickname': self.nickname,
            'avatar': self.avatar
        } 

    def get_dictation_config(self):
        """获取用户的听写配置，如果不存在则创建默认配置"""
        if not self.dictation_config:
            from app.models.dictation_config import DictationConfig
            self.dictation_config = DictationConfig(user_id=self.id)
        return self.dictation_config 
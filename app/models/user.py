from datetime import datetime
from ..extensions import db

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'nickname': self.nickname,
            'avatar': self.avatar
        } 
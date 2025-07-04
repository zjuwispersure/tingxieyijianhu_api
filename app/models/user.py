from datetime import datetime
from .base import BaseModel
from app.extensions import db

class User(BaseModel):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(100), unique=True, nullable=False)
    nickname = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    
    # 添加与 Child 的关系
    children = db.relationship('Child', back_populates='user', lazy=True)
    
    # 添加与家庭关系的关联
    family_relations = db.relationship('UserFamilyRelation', back_populates='user')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'nickname': self.nickname,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'openid': self.openid
        } 
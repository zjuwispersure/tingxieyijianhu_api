from .base import BaseModel
from .database import db
from datetime import datetime

class Achievement(BaseModel):
    """成就模型"""
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)  # 添加孩子ID
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(128))
    icon = db.Column(db.String(128))
    condition = db.Column(db.String(256))  # 达成条件
    
    # 关联关系
    child = db.relationship('Child', backref='achievements')
    
    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'condition': self.condition,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 
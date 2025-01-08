from .database import db
from datetime import datetime

class Achievement(db.Model):
    """成就模型"""
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 成就名称
    description = db.Column(db.String(200))  # 成就描述
    type = db.Column(db.String(20), nullable=False)  # 成就类型
    condition = db.Column(db.String(200))  # 解锁条件
    reward = db.Column(db.Integer, default=0)  # 奖励积分
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'condition': self.condition,
            'reward': self.reward
        } 
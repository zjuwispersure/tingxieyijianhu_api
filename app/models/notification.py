from .base import BaseModel
from .database import db
from datetime import datetime

class Notification(BaseModel):
    """通知模型"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)  # 通知标题
    content = db.Column(db.Text)  # 通知内容
    type = db.Column(db.String(20), nullable=False)  # 通知类型
    is_read = db.Column(db.Boolean, default=False)  # 是否已读

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
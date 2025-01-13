from datetime import datetime
from ..extensions import db

class BaseModel(db.Model):
    """基础模型类"""
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now) 
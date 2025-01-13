from datetime import datetime
from ..extensions import db
from .base import BaseModel

class Child(BaseModel):
    __tablename__ = 'children'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    child_id = db.Column(db.Integer, nullable=False)  # 用户下的孩子序号
    nickname = db.Column(db.String(32), nullable=False)
    province = db.Column(db.String(32))
    city = db.Column(db.String(32))
    grade = db.Column(db.Integer)
    semester = db.Column(db.Integer)
    textbook_version = db.Column(db.String(32))
    
    # 关系
    dictation_tasks = db.relationship('DictationTask', back_populates='child', lazy=True)
    dictation_config = db.relationship('DictationConfig', back_populates='child', uselist=False)
    user = db.relationship('User', back_populates='children')
    family = db.relationship('Family', back_populates='children')  # 添加与Family的关系
    
    # 添加联合唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'family_id', name='unique_user_family_child'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'nickname': self.nickname,
            'province': self.province,
            'city': self.city,
            'grade': self.grade,
            'semester': self.semester,
            'textbook_version': self.textbook_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
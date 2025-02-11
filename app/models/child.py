from datetime import datetime
from .database import db
from .base import BaseModel
from .dictation import DictationSession
from sqlalchemy.orm import validates

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
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # 添加软删除字段
    
    # 关系
    dictation_sessions = db.relationship('DictationSession', back_populates='child')
    dictation_config = db.relationship('DictationConfig', back_populates='child', 
                                      primaryjoin="and_(Child.id==DictationConfig.child_id)")
    user = db.relationship('User', back_populates='children')
    family = db.relationship('Family', back_populates='children')
    
    # 修改唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'child_id', name='unique_user_child'),  # 一个用户下的child_id要唯一
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
    
    @classmethod
    def check_nickname_exists(cls, family_id: int, nickname: str, exclude_id: int = None) -> bool:
        """检查昵称在家庭内是否已存在
        
        Args:
            family_id: 家庭ID
            nickname: 要检查的昵称
            exclude_id: 排除的孩子ID（用于更新时）
            
        Returns:
            bool: 昵称是否已存在
        """
        query = cls.query.filter_by(
            family_id=family_id,
            nickname=nickname.strip(),
            is_deleted=False
        )
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
            
        return query.first() is not None
    
    @validates('nickname')
    def validate_nickname(self, key, nickname):
        if not nickname or len(nickname.strip()) == 0:
            raise ValueError('昵称不能为空')
        if len(nickname) > 32:
            raise ValueError('昵称长度不能超过32个字符')
        
        # 检查昵称在家庭内是否唯一
        if hasattr(self, 'family_id') and self.family_id:
            if Child.check_nickname_exists(self.family_id, nickname, self.id):
                raise ValueError('该昵称在家庭内已存在')
                
        return nickname.strip() 
from datetime import datetime
from .base import BaseModel
from .database import db
from flask import current_app

class Family(BaseModel):
    """家庭模型"""
    __tablename__ = 'families'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 关系
    members = db.relationship('FamilyMember', backref='family', lazy=True)
    children = db.relationship('Child', back_populates='family', lazy=True)
    creator = db.relationship('User', 
        foreign_keys=[created_by],
        backref=db.backref('created_families', lazy=True)
    )
    user_relations = db.relationship('UserFamilyRelation', back_populates='family')

    @classmethod
    def create_default_family(cls, user):
        """为用户创建默认家庭并建立关系"""
        try:
            # 创建默认家庭
            family = cls(
                name=f"{user.nickname or '我'}的家庭",
                created_by=user.id
            )
            db.session.add(family)
            db.session.flush()  # 获取 family.id
            
            # 创建用户-家庭关系
            relation = UserFamilyRelation(
                user_id=user.id,
                family_id=family.id,
                role='parent',
                is_admin=True
            )
            db.session.add(relation)
            db.session.commit()
            
            return family, relation
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建默认家庭失败: {str(e)}")
            raise

class UserFamilyRelation(BaseModel):
    """用户与家庭的关系表"""
    __tablename__ = 'user_family_relations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    role = db.Column(db.String(32), nullable=False)  # admin/member
    is_admin = db.Column(db.Boolean, default=False)  # 是否是家庭管理员
    
    # 关系
    user = db.relationship('User', back_populates='family_relations')
    family = db.relationship('Family', back_populates='user_relations')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'family_id', name='unique_user_family_relation'),
    )

class FamilyMember(BaseModel):
    """家庭成员模型（合并后）"""
    __tablename__ = 'family_members'
    
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 可以为空，表示未注册的孩子
    name = db.Column(db.String(32), nullable=False)
    role = db.Column(db.String(32), nullable=False)  # child/parent/grandparent等
    is_admin = db.Column(db.Boolean, default=False)  # 是否是家庭管理员
    is_child = db.Column(db.Boolean, default=False)  # 是否是被管理的孩子
    
    # 听写记录关系
    dictation_records = db.relationship('DictationRecord', 
                                      foreign_keys='DictationRecord.child_id',
                                      backref='child', lazy=True)
    
    # 唯一约束
    __table_args__ = (db.UniqueConstraint('user_id', 'family_id', name='unique_user_family'),)

class DictationRecord(BaseModel):
    """听写记录模型"""
    __tablename__ = 'dictation_records'
    
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('family_members.id'), nullable=False)
    recorder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    yuwen_item_id = db.Column(db.Integer, db.ForeignKey('yuwen_items.id'), nullable=False)
    score = db.Column(db.Integer) 
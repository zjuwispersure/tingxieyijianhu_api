from .database import db
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

class Child(db.Model):
    """孩子模型
    
    用于存储孩子的基本信息和学习配置
    
    Attributes:
        id: 主键ID
        child_id: 用户下的孩子序号
        user_id: 关联的用户ID
        nickname: 昵称
        province: 省份
        city: 城市
        grade: 年级
        semester: 学期
        textbook_version: 教材版本
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = 'children'
    
    # 基本信息
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, nullable=False)  # 用户下的孩子序号
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    nickname = Column(String(50), nullable=False)
    province = Column(String(50))
    city = Column(String(50))
    grade = Column(Integer)
    semester = Column(Integer)
    textbook_version = Column(String(20))
    
    # 时间戳
    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 约束
    __table_args__ = (
        UniqueConstraint('user_id', 'child_id', name='uix_user_child_id'),
        UniqueConstraint('user_id', 'nickname', name='uix_user_nickname'),
    )
    
    # 关联关系
    user = relationship("User", back_populates="children")
    dictation_tasks = relationship("DictationTask", back_populates="child", cascade="all, delete-orphan")
    dictation_config = relationship(
        "DictationConfig",
        uselist=False,
        back_populates="child",
        cascade="all, delete-orphan"
    )
    
    def __init__(self, **kwargs):
        """初始化孩子实例
        
        Args:
            **kwargs: 关键字参数，用于设置属性
        """
        super(Child, self).__init__(**kwargs)
        
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含模型属性的字典
        """
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
    def get_next_child_id(cls, user_id):
        """获取用户的下一个可用 child_id
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 下一个可用的 child_id
        """
        max_child = cls.query.filter_by(user_id=user_id).order_by(cls.child_id.desc()).first()
        return (max_child.child_id + 1) if max_child else 1
        
    def validate(self):
        """验证模型数据
        
        Returns:
            tuple: (是否有效, 错误信息)
        """
        if not self.nickname:
            return False, "昵称不能为空"
            
        if not self.grade or not isinstance(self.grade, int):
            return False, "年级必须是有效的整数"
            
        if not self.semester or self.semester not in [1, 2]:
            return False, "学期必须是1或2"
            
        if not self.textbook_version:
            return False, "教材版本不能为空"
            
        return True, None
        
    def __repr__(self):
        """模型的字符串表示
        
        Returns:
            str: 模型的字符串表示
        """
        return f'<Child {self.nickname}>' 
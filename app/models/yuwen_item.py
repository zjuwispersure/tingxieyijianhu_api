from typing import List, Optional
from sqlalchemy import and_
from .base import BaseModel
from .database import db
from flask import current_app

class YuwenItem(BaseModel):
    """存储教材原始数据"""
    __tablename__ = 'yuwen_items'

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), nullable=False)  # 词语/字
    pinyin = db.Column(db.String(100))  # 拼音
    type = db.Column(db.String(20), nullable=False)  # 类型:识字/写字/词语
    unit = db.Column(db.Integer, nullable=False)  # 单元
    lesson = db.Column(db.Integer, nullable=False)  # 第几课
    lesson_name = db.Column(db.String(100))  # 课文名称
    grade = db.Column(db.Integer, nullable=False)  # 年级
    semester = db.Column(db.Integer, nullable=False)  # 学期
    textbook_version = db.Column(db.String(20), nullable=False)  # 教材版本
    audio_url = db.Column(db.String(200))  # 音频URL
    
    def __repr__(self):
        return f'<YuwenItem {self.word}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'word': self.word,
            'pinyin': self.pinyin,
            'type': self.type,
            'unit': self.unit,
            'lesson': self.lesson,
            'lesson_name': self.lesson_name,
            'grade': self.grade,
            'semester': self.semester,
            'textbook_version': self.textbook_version,
            'audio_url': self.audio_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 

    @classmethod
    def get_items_by_lesson(cls, grade: int, semester: int, 
                           textbook_version: str, unit: int, 
                           lesson: Optional[int] = None) -> List['YuwenItem']:
        """
        根据年级、学期、教材版本、单元和课次获取词语列表
        
        Args:
            grade: 年级
            semester: 学期
            textbook_version: 教材版本
            unit: 单元号
            lesson: 课次号（可选）
            
        Returns:
            List[YuwenItem]: 词语列表
        """
        query = cls.query.filter(and_(
            cls.grade == grade,
            cls.semester == semester,
            cls.textbook_version == textbook_version,
            cls.unit == unit
        ))
        
        if lesson is not None:
            query = query.filter(cls.lesson == lesson)
            
        return query.order_by(cls.lesson, cls.id).all()

    @classmethod
    def get_lesson_list(cls, grade: int, semester: int, 
                       textbook_version: str, unit: int) -> List[dict]:
        """获取指定单元下的所有课次列表"""
        try:
            items = db.session.query(
                cls.lesson,
                cls.lesson_name
            ).filter(and_(
                cls.grade == grade,
                cls.semester == semester,
                cls.textbook_version == textbook_version,
                cls.unit == unit
            )).distinct().order_by(cls.lesson).all()
            
            return [
                {'lesson': item.lesson, 
                 'name': item.lesson_name,
                 'unit': item.unit}
                for item in items
            ]
        except Exception as e:
            current_app.logger.error(f"Database error in get_lesson_list: {str(e)}", exc_info=True)
            raise 

    @classmethod
    def get_all_lessons(cls, grade: int, semester: int, textbook_version: str) -> List[dict]:
        """获取指定年级学期下的所有课次信息
        
        Returns:
            List[dict]: 包含 unit, lesson, lesson_name 的列表
        """
        try:
            items = db.session.query(
                cls.unit,
                cls.lesson,
                cls.lesson_name
            ).filter(and_(
                cls.grade == grade,
                cls.semester == semester,
                cls.textbook_version == textbook_version
            )).distinct().order_by(cls.unit, cls.lesson).all()
            
            return [
                {
                    'unit': item.unit,
                    'lesson': item.lesson,
                    'name': item.lesson_name
                }
                for item in items
            ]
        except Exception as e:
            current_app.logger.error(f"Error in get_all_lessons: {str(e)}", exc_info=True)
            raise

    @classmethod
    def get_items_by_lesson_id(cls, grade: int, semester: int, 
                              textbook_version: str, lesson: int) -> List['YuwenItem']:
        """根据课次ID获取词语列表"""
        try:
            return cls.query.filter(and_(
                cls.grade == grade,
                cls.semester == semester,
                cls.textbook_version == textbook_version,
                cls.lesson == lesson
            )).order_by(cls.id).all()
        except Exception as e:
            current_app.logger.error(f"Error in get_items_by_lesson_id: {str(e)}", exc_info=True)
            raise

    @classmethod
    def get_items_by_unit(cls, grade: int, semester: int,
                         textbook_version: str, unit: int) -> List['YuwenItem']:
        """根据单元获取词语列表"""
        try:
            return cls.query.filter(and_(
                cls.grade == grade,
                cls.semester == semester,
                cls.textbook_version == textbook_version,
                cls.unit == unit
            )).order_by(cls.lesson, cls.id).all()
        except Exception as e:
            current_app.logger.error(f"Error in get_items_by_unit: {str(e)}", exc_info=True)
            raise 

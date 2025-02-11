from typing import List, Optional
from sqlalchemy import and_
from .base import BaseModel
from .database import db
from flask import current_app
from ..utils.oss import get_signed_url

class YuwenItem(BaseModel):
    """存储教材原始数据"""
    __tablename__ = 'yuwen_items'

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(32), nullable=False)  # 汉字/词语
    pinyin = db.Column(db.String(64))  # 拼音
    hint = db.Column(db.String(128))  # 提示信息
    type = db.Column(db.String(32))  # 类型：识字/写字/词语
    unit = db.Column(db.String(32))  # 单元
    lesson = db.Column(db.Integer)  # 课文序号
    lesson_name = db.Column(db.String(64))  # 课文名称
    grade = db.Column(db.Integer)  # 年级
    semester = db.Column(db.Integer)  # 学期
    textbook_version = db.Column(db.String(32))  # 教材版本
    audio_url = db.Column(db.String(256))  # 音频URL
    
    # 关系
    dictation_details = db.relationship('DictationDetail', back_populates='yuwen_item')
    
    def __repr__(self):
        return f'<YuwenItem {self.word}>'

    def to_dict(self):
        """转换为字典"""
        current_app.logger.debug(f"Converting YuwenItem to dict, audio_url: {self.audio_url}")
        audio_url = get_signed_url(self.audio_url) if self.audio_url else None
        current_app.logger.debug(f"Signed audio_url: {audio_url}")
        
        return {
            'id': self.id,
            'word': self.word,
            'pinyin': self.pinyin,
            'hint': self.hint,
            'type': self.type,
            'unit': self.unit,
            'lesson': self.lesson,
            'lesson_name': self.lesson_name,
            'audio_url': audio_url
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
                              textbook_version: str, lesson: int,
                              type: Optional[str] = None) -> List['YuwenItem']:
        """根据课次ID获取词语列表"""
        try:
            current_app.logger.info(f"Querying items with params: grade={grade}, semester={semester}, "
                                  f"textbook_version={textbook_version}, lesson={lesson}, type={type}")
            query = cls.query.filter(and_(
                cls.grade == grade,
                cls.semester == semester,
                cls.textbook_version == textbook_version,
                cls.lesson == lesson
            ))
            
            if type:
                query = query.filter(cls.type == type)
                
            items = query.order_by(cls.id).all()
            current_app.logger.info(f"Found {len(items)} items")
            return items
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

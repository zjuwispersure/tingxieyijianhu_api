from .database import db
from sqlalchemy import Column, Integer, String

class YuwenItem(db.Model):
    """语文学习项目（字/词）表"""
    __tablename__ = 'yuwen_items'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(50), nullable=False)  # 字或词
    type = Column(String(20), nullable=False)  # 识字/写字/词语
    book_version = Column(String(20), nullable=False)  # 教材版本
    grade = Column(Integer, nullable=False)  # 年级
    semester = Column(Integer, nullable=False)  # 学期
    unit = Column(String(20), nullable=False)  # Unit 1, 语文园地一 等
    pinyin = Column(String(100))  # 拼音
    hint = Column(String(200))  # 提示词
    audio_path = Column(String(200))  # 音频路径 
    audio_url = Column(String(500))  # 完整的音频文件 URL 
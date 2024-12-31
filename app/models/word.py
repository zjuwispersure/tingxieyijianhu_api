from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Word(Base):
    """词语表"""
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(50), nullable=False)
    subject = Column(String(20), nullable=False)  # yuwen/english
    grade = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    unit = Column(Integer)
    pinyin = Column(String(100))
    
    # 关联关系
    learning_status = relationship("WordLearningStatus", back_populates="word")

class WordCharacter(Base):
    __tablename__ = 'word_characters'
    
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    position = Column(Integer, nullable=False)
    
    word = relationship("Word", back_populates="characters")
    character = relationship("Character", back_populates="word_characters") 
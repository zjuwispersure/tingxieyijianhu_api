from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Word(Base):
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(50), nullable=False, unique=True)
    
    characters = relationship("WordCharacter", back_populates="word")

class WordCharacter(Base):
    __tablename__ = 'word_characters'
    
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    position = Column(Integer, nullable=False)
    
    word = relationship("Word", back_populates="characters")
    character = relationship("Character", back_populates="word_characters") 
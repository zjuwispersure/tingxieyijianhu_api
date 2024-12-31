from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class DictationHint(Base):
    __tablename__ = 'dictation_hints'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    hint_word = Column(String(50), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    character = relationship("Character", back_populates="dictation_hints") 
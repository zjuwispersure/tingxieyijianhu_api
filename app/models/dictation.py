from datetime import datetime
from .base import Base
from .database import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class DictationHint(Base):
    __tablename__ = 'dictation_hints'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    hint_word = Column(String(50), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    character = relationship("Character", back_populates="dictation_hints") 
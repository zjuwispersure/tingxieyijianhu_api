from .database import db
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class CharacterListType(db.Model):
    __tablename__ = 'character_list_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    
    # 不使用 back_populates，避免循环依赖
    character_lists = relationship("CharacterList") 
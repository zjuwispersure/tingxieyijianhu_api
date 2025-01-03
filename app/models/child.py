from .database import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Child(db.Model):
    __tablename__ = 'children'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(50), nullable=False)
    grade = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    
    user = relationship("User", back_populates="children")
    dictation_tasks = relationship("DictationTask", back_populates="child") 
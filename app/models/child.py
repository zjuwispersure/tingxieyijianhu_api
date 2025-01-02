from datetime import datetime
from ..extensions import db
from sqlalchemy.orm import relationship

class Child(db.Model):
    __tablename__ = 'children'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    nickname = db.Column(db.String(64), nullable=False)
    school_province = db.Column(db.String(32))
    school_city = db.Column(db.String(32))
    grade = db.Column(db.String(16))
    semester = db.Column(db.String(16))
    textbook_version = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    dictations = db.relationship('Dictation', backref='child', lazy=True)
    dictation_tasks = relationship("DictationTask", back_populates="child")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nickname': self.nickname,
            'school_province': self.school_province,
            'school_city': self.school_city,
            'grade': self.grade,
            'semester': self.semester,
            'textbook_version': self.textbook_version
        } 
from datetime import datetime
from ..extensions import db

class Dictation(db.Model):
    __tablename__ = 'dictations'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    mode = db.Column(db.String(16), nullable=False)
    word_count = db.Column(db.Integer, nullable=False)
    repeat_count = db.Column(db.Integer, nullable=False)
    interval = db.Column(db.Integer, nullable=False)
    prioritize_errors = db.Column(db.Boolean, default=False)
    content = db.Column(db.JSON)
    result = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'mode': self.mode,
            'word_count': self.word_count,
            'repeat_count': self.repeat_count,
            'interval': self.interval,
            'prioritize_errors': self.prioritize_errors,
            'content': self.content,
            'result': self.result,
            'created_at': self.created_at.isoformat()
        } 
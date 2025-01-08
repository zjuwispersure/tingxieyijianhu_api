from .database import db
from datetime import datetime

class YuwenItem(db.Model):
    """语文学习项目模型 - 存储教材原始数据"""
    __tablename__ = 'yuwen_items'

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), nullable=False, index=True)  # 词语
    pinyin = db.Column(db.String(100))  # 拼音
    audio_url = db.Column(db.String(255))  # 音频URL
    
    # 教材信息
    grade = db.Column(db.Integer, nullable=False)  # 年级
    semester = db.Column(db.Integer, nullable=False)  # 学期
    unit = db.Column(db.Integer, nullable=False)  # 单元
    textbook_version = db.Column(db.String(20), nullable=False)  # 教材版本
    type = db.Column(db.String(20), nullable=False)  # 类型(识字/写字/词语)
    
    # 时间戳
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<YuwenItem {self.word}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'word': self.word,
            'pinyin': self.pinyin,
            'audio_url': self.audio_url,
            'grade': self.grade,
            'semester': self.semester,
            'unit': self.unit,
            'textbook_version': self.textbook_version,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 
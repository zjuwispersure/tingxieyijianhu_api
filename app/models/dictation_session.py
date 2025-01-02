from datetime import datetime
from .base import Base
from .database import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

class DictationSession(Base):
    """听写会话表 - 记录每次听写的基本信息"""
    __tablename__ = 'dictation_sessions'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('dictation_tasks.id'), nullable=False)
    
    # 听写基本信息
    start_time = Column(DateTime, default=datetime.utcnow)  # 开始时间
    end_time = Column(DateTime)                            # 结束时间
    total_words = Column(Integer)                         # 总词语数
    correct_count = Column(Integer)                       # 正确数量
    accuracy_rate = Column(Float)                         # 正确率
    
    # 状态
    status = Column(String(20), default='进行中')          # 进行中/已完成/中断

    # 关联关系
    task = relationship("DictationTask", back_populates="sessions")
    details = relationship("DictationDetail", back_populates="session")

    def calculate_stats(self):
        """计算听写统计信息"""
        if self.details:
            self.total_words = len(self.details)
            self.correct_count = sum(1 for detail in self.details if detail.is_correct)
            self.accuracy_rate = self.correct_count / self.total_words if self.total_words > 0 else 0

class DictationDetail(Base):
    """听写详情表 - 记录每个词语的听写结果"""
    __tablename__ = 'dictation_details'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('dictation_sessions.id'), nullable=False)
    word = Column(String(50), nullable=False)              # 听写词语
    
    # 听写结果
    user_input = Column(String(50))                        # 用户输入
    writing_order = Column(String(200))                    # 书写顺序记录
    image_path = Column(String(200))                       # 听写图片路径
    
    # 批改信息
    is_correct = Column(Integer, default=None)             # 是否正确(None表示未批改)
    corrector_id = Column(Integer, ForeignKey('user.id'))  # 批改人ID
    correction_time = Column(DateTime)                     # 批改时间
    correction_note = Column(String(200))                  # 批改备注
    
    # AI识别相关
    ai_result = Column(String(50))                        # AI识别结果
    ai_confidence = Column(Float)                         # AI识别置信度
    ai_verified = Column(Boolean, default=False)          # AI结果是否已人工确认
    
    # 其他信息
    retry_count = Column(Integer, default=0)              # 重试次数
    start_time = Column(DateTime)                         # 开始时间
    submit_time = Column(DateTime)                        # 提交时间
    
    # 关联关系
    session = relationship("DictationSession", back_populates="details")
    corrector = relationship("User", foreign_keys=[corrector_id])

    def verify_ai_result(self, corrector_id, is_correct, note=None):
        """人工确认AI识别结果"""
        self.is_correct = is_correct
        self.corrector_id = corrector_id
        self.correction_time = datetime.utcnow()
        self.correction_note = note
        self.ai_verified = True

    def manual_correction(self, corrector_id, is_correct, note=None):
        """人工批改"""
        self.is_correct = is_correct
        self.corrector_id = corrector_id
        self.correction_time = datetime.utcnow()
        self.correction_note = note 
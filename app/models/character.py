from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class CharacterListType(Base):
    __tablename__ = 'character_list_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String)
    
    character_lists = relationship("CharacterList", back_populates="list_type")

class Character(Base):
    __tablename__ = 'characters'
    
    id = Column(Integer, primary_key=True)
    character = Column(String(1), nullable=False, unique=True)
    pinyin_initial = Column(String(10))  # 声母
    pinyin_final = Column(String(10))    # 韵母
    pinyin_tone = Column(Integer)        # 声调
    stroke_count = Column(Integer)
    
    list_items = relationship("CharacterListItem", back_populates="character")
    word_characters = relationship("WordCharacter", back_populates="character")
    dictation_hints = relationship("DictationHint", back_populates="character")
    audio_files = relationship("CharacterAudio", back_populates="character")

    @property
    def pinyin(self):
        """返回完整拼音（带声调）"""
        if not (self.pinyin_initial and self.pinyin_final and self.pinyin_tone):
            return None
            
        # 声母可能为空（如"安"的拼音）
        base = self.pinyin_initial + self.pinyin_final if self.pinyin_initial else self.pinyin_final
        
        # 声调处理规则
        TONE_MARKS = {
            'a': 'āáǎà',
            'e': 'ēéěè',
            'i': 'īíǐì',
            'o': 'ōóǒò',
            'u': 'ūúǔù',
            'ü': 'ǖǘǚǜ'
        }
        
        if self.pinyin_tone == 5:  # 轻声
            return base
            
        # 找到要标声调的韵母字母
        tone_char = None
        if 'a' in base:
            tone_char = 'a'
        elif 'e' in base:
            tone_char = 'e'
        elif 'ou' in base:
            tone_char = 'o'
        else:
            for c in base:
                if c in 'iouü':
                    tone_char = c
                    break
                    
        if tone_char:
            # 替换对应字母为带声调的字母
            return base.replace(
                tone_char, 
                TONE_MARKS[tone_char][self.pinyin_tone - 1]
            )
        return base

    @classmethod
    def create_with_pinyin(cls, character, pinyin):
        """通过完整拼音创建汉字实例"""
        # 解析拼音字符串，提取声母、韵母和声调
        # 这里需要一个拼音解析库，如 pypinyin
        from pypinyin import pinyin, Style
        
        result = pinyin(character, style=Style.TONE3, heteronym=False)[0][0]
        
        # 分离声母和韵母
        initials = ['b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 
                   'j', 'q', 'x', 'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w']
        
        tone = int(result[-1]) if result[-1].isdigit() else 5
        base = result[:-1] if result[-1].isdigit() else result
        
        initial = ''
        final = base
        
        for i in initials:
            if base.startswith(i):
                initial = i
                final = base[len(i):]
                break
        
        return cls(
            character=character,
            pinyin_initial=initial,
            pinyin_final=final,
            pinyin_tone=tone
        )

class CharacterList(Base):
    __tablename__ = 'character_lists'
    
    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey('character_list_types.id'), nullable=False)
    grade = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    unit = Column(Integer, nullable=False)
    
    list_type = relationship("CharacterListType", back_populates="character_lists")
    list_items = relationship("CharacterListItem", back_populates="character_list")

class CharacterListItem(Base):
    __tablename__ = 'character_list_items'
    
    id = Column(Integer, primary_key=True)
    list_id = Column(Integer, ForeignKey('character_lists.id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    character_list = relationship("CharacterList", back_populates="list_items")
    character = relationship("Character", back_populates="list_items") 

class CharacterAudio(Base):
    __tablename__ = 'character_audio'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    audio_path = Column(String(255), nullable=False)
    audio_type = Column(String(20), nullable=False)
    duration = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    character = relationship("Character", back_populates="audio_files") 
import os
import sys
import pandas as pd
from pypinyin import pinyin, Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.models import Word, Character, WordCharacter, CharacterList, CharacterListItem, db

def get_pinyin(text):
    """获取拼音"""
    return ' '.join([p[0] for p in pinyin(text, style=Style.TONE3)])

def import_characters(shizi_path, xiezi_path, audio_base_dir, grade, semester):
    """导入识字表和写字表"""
    print(f"Importing characters for grade {grade} semester {semester}")
    
    # 读取识字表
    shizi_df = pd.read_csv(shizi_path, names=['character', 'unit'], dtype={'character': str, 'unit': int})
    
    # 读取写字表
    xiezi_df = pd.read_csv(xiezi_path, names=['character', 'unit'], dtype={'character': str, 'unit': int})
    
    # 创建字表类型
    shizi_type = CharacterList.query.filter_by(
        name='识字',
        grade=grade,
        semester=semester
    ).first()
    if not shizi_type:
        shizi_type = CharacterList(name='识字', grade=grade, semester=semester)
        db.session.add(shizi_type)
    
    xiezi_type = CharacterList.query.filter_by(
        name='写字',
        grade=grade,
        semester=semester
    ).first()
    if not xiezi_type:
        xiezi_type = CharacterList(name='写字', grade=grade, semester=semester)
        db.session.add(xiezi_type)
    
    db.session.flush()
    
    # 导入识字表
    for _, row in shizi_df.iterrows():
        char = row['character'].strip()
        unit = row['unit']
        
        # 查找音频文件
        audio_path = os.path.join(audio_base_dir, f"{char}.mp3")
        if not os.path.exists(audio_path):
            print(f"Warning: Audio file not found for character: {char}")
        
        # 查找或创建汉字
        character = Character.query.filter_by(character=char).first()
        if not character:
            character = Character(
                character=char,
                pinyin=get_pinyin(char),
                audio_path=audio_path if os.path.exists(audio_path) else None
            )
            db.session.add(character)
            db.session.flush()
        
        # 创建识字表项
        item = CharacterListItem.query.filter_by(
            list_id=shizi_type.id,
            character_id=character.id,
            unit=unit
        ).first()
        if not item:
            item = CharacterListItem(
                list_id=shizi_type.id,
                character_id=character.id,
                unit=unit
            )
            db.session.add(item)
    
    # 导入写字表
    for _, row in xiezi_df.iterrows():
        char = row['character'].strip()
        unit = row['unit']
        
        # 查找汉字（应该已经在识字表中创建）
        character = Character.query.filter_by(character=char).first()
        if not character:
            print(f"Warning: Character {char} not found in database")
            continue
        
        # 创建写字表项
        item = CharacterListItem.query.filter_by(
            list_id=xiezi_type.id,
            character_id=character.id,
            unit=unit
        ).first()
        if not item:
            item = CharacterListItem(
                list_id=xiezi_type.id,
                character_id=character.id,
                unit=unit
            )
            db.session.add(item)
    
    db.session.commit()
    print("Characters imported successfully")

def import_words(ciyu_path, audio_base_dir, grade, semester):
    """导入词语表"""
    print(f"Importing words for grade {grade} semester {semester}")
    
    # 读取词语表
    df = pd.read_csv(ciyu_path, names=['word', 'unit'], dtype={'word': str, 'unit': int})
    
    for _, row in df.iterrows():
        word = row['word'].strip()
        unit = row['unit']
        
        # 查找音频文件
        audio_path = os.path.join(audio_base_dir, f"{word}.mp3")
        if not os.path.exists(audio_path):
            print(f"Warning: Audio file not found for word: {word}")
            continue
        
        # 检查词语是否已存在
        word_obj = Word.query.filter_by(
            word=word,
            grade=grade,
            semester=semester,
            unit=unit
        ).first()
        
        if not word_obj:
            # 创建新词语记录
            word_obj = Word(
                word=word,
                subject='yuwen',
                grade=grade,
                semester=semester,
                unit=unit,
                pinyin=get_pinyin(word),
                audio_path=audio_path
            )
            db.session.add(word_obj)
            db.session.flush()
            
            # 为词语中的每个字创建关联
            for i, char in enumerate(word):
                # 查找汉字（应该已经通过 import_characters 导入）
                character = Character.query.filter_by(character=char).first()
                if not character:
                    print(f"Warning: Character {char} not found in database")
                    continue
                
                # 创建词语-汉字关联
                word_char = WordCharacter(
                    word_id=word_obj.id,
                    character_id=character.id,
                    position=i
                )
                db.session.add(word_char)
        else:
            # 更新已存在词语的音频路径
            word_obj.audio_path = audio_path
    
    db.session.commit()
    print("Words imported successfully")

def main():
    app = create_app()
    with app.app_context():
        grade = 4
        semester = 1
        base_path = f"data/yuwen/renjiaoban/grade_{grade}_{semester}"
        
        # 检查文件是否存在
        shizi_path = os.path.join(base_path, "shizibiao.txt")
        xiezi_path = os.path.join(base_path, "xiezibiao.txt")
        ciyu_path = os.path.join(base_path, "ciyubiao.txt")
        
        char_audio_dir = "audio_汉字"
        word_audio_dir = "audio_词语"
        
        # 导入识字和写字
        if os.path.exists(shizi_path) and os.path.exists(xiezi_path):
            import_characters(shizi_path, xiezi_path, char_audio_dir, grade, semester)
        else:
            print("Character list files not found")
        
        # 导入词语
        if os.path.exists(ciyu_path):
            import_words(ciyu_path, word_audio_dir, grade, semester)
        else:
            print("Word list file not found")

if __name__ == '__main__':
    main() 
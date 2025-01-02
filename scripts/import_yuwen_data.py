import os
import sys
import pandas as pd
from pypinyin import pinyin, Style
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.models import Word, Character, WordCharacter, CharacterList, CharacterListItem, db

# 加载环境变量
load_dotenv()

def get_pinyin(text):
    """获取拼音"""
    return ' '.join([p[0] for p in pinyin(text, style=Style.TONE3)])

def import_characters(char_path, list_name, audio_base_dir, subject, book_version, grade, semester):
    """导入字表数据
    Args:
        char_path: 字表文件路径（识字表或写字表）
        list_name: 字表类型名称（'识字' 或 '写字'）
        audio_base_dir: 音频文件目录
        subject: 学科
        book_version: 教材版本
        grade: 年级
        semester: 学期
    """
    print(f"Importing {list_name} for {subject} {book_version} grade {grade} semester {semester}")
    
    # 读取字表
    df = pd.read_csv(char_path, names=['character', 'unit'], dtype={'character': str, 'unit': int})
    
    # 创建字表类型
    char_list = CharacterList.query.filter_by(
        name=list_name,
        subject=subject,
        book_version=book_version,
        grade=grade,
        semester=semester
    ).first()
    
    if not char_list:
        char_list = CharacterList(
            name=list_name,
            subject=subject,
            book_version=book_version,
            grade=grade,
            semester=semester
        )
        db.session.add(char_list)
        db.session.flush()
    
    # 导入字表内容
    for _, row in df.iterrows():
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
        
        # 创建字表项
        item = CharacterListItem.query.filter_by(
            list_id=char_list.id,
            character_id=character.id,
            unit=unit
        ).first()
        if not item:
            item = CharacterListItem(
                list_id=char_list.id,
                character_id=character.id,
                unit=unit
            )
            db.session.add(item)
    
    db.session.commit()
    print(f"{list_name} imported successfully")

def import_words(ciyu_path, audio_dir, subject, textbook, grade, semester):
    """导入词语表"""
    print(f"Importing words for {subject} {textbook} grade {grade} semester {semester}")
    
    # 读取词语表
    df = pd.read_csv(ciyu_path, names=['word', 'unit'], dtype={'word': str, 'unit': int})
    
    for _, row in df.iterrows():
        word = row['word'].strip()
        unit = row['unit']
        
        # 查找音频文件
        audio_path = os.path.join(audio_dir, f"{word}.mp3")
        if not os.path.exists(audio_path):
            print(f"Warning: Audio file not found for word: {word}")
            continue
        
        # 检查词语是否已存在
        word_obj = Word.query.filter_by(
            word=word,
            subject=subject,
            textbook=textbook,
            grade=grade,
            semester=semester,
            unit=unit
        ).first()
        
        if not word_obj:
            # 创建新词语记录
            word_obj = Word(
                word=word,
                subject=subject,
                textbook=textbook,
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
                character = Character.query.filter_by(character=char).first()
                if not character:
                    print(f"Warning: Character {char} not found in database")
                    continue
                
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
    # 从环境变量获取基础路径
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    AUDIO_DIR = os.getenv('AUDIO_DIR', 'data')
    
    # 导入参数
    subject = 'yuwen'
    book_version = 'renjiaoban'
    grade = 4
    semester = 1
    
    base_path  = os.path.join(
        DATA_DIR,
        subject,
        book_version,
        f"grade_{grade}_{semester}"
    ) 
    # 构建路径
    audio_base_path = os.path.join(
        AUDIO_DIR,
        subject,
        book_version,
        f"grade_{grade}_{semester}"
    )
    
    # 音频目录
    audio_dirs = {
        '识字': os.path.join(audio_base_path, '_识字'),
        '写字': os.path.join(audio_base_path, '_写字'),
        '词语': os.path.join(audio_base_path, '_词语')
    }
    
    app = create_app()
    with app.app_context():
        # 导入识字表
        shizi_path = os.path.join(base_path, "shizibiao.txt")
        if os.path.exists(shizi_path):
            import_characters(
                shizi_path, '识字', audio_dirs['识字'],
                subject, book_version, grade, semester
            )
        else:
            print("识字表 file not found")
        
        # 导入写字表
        xiezi_path = os.path.join(base_path, "xiezibiao.txt")
        if os.path.exists(xiezi_path):
            import_characters(
                xiezi_path, '写字', audio_dirs['写字'],
                subject, book_version, grade, semester
            )
        else:
            print("写字表 file not found")
        
        # 导入词语表
        ciyu_path = os.path.join(base_path, "ciyubiao.txt")
        if os.path.exists(ciyu_path):
            import_words(
                ciyu_path, audio_dirs['词语'],
                subject, book_version, grade, semester
            )
        else:
            print("词语表 file not found")

if __name__ == '__main__':
    main() 
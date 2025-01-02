import os
import sys
import pandas as pd
from pypinyin import pinyin, Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.models import Word, Character, WordCharacter, db

def get_pinyin(word):
    """获取词语拼音"""
    return ' '.join([p[0] for p in pinyin(word, style=Style.TONE3)])

def import_words(file_path, audio_base_dir, grade, semester):
    """导入词语数据并关联音频文件"""
    app = create_app()
    
    with app.app_context():
        # 读取词语表
        df = pd.read_csv(file_path, names=['word', 'unit'], dtype={'word': str, 'unit': int})
        
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
        print(f"Successfully imported words for grade {grade} semester {semester}")

def main():
    # 导入四年级上册的词语
    grade = 4
    semester = 1
    
    file_path = "data/yuwen/renjiaoban/grade_4_1/ciyubiao.txt"
    audio_base_dir = "audio_词语"
    
    if not os.path.exists(file_path):
        print(f"Error: Word list file not found: {file_path}")
        return
        
    if not os.path.exists(audio_base_dir):
        print(f"Error: Audio directory not found: {audio_base_dir}")
        return
        
    import_words(file_path, audio_base_dir, grade, semester)

if __name__ == '__main__':
    main() 
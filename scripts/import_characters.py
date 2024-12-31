from app import db
from app import create_app
from app.models import Character, CharacterList, CharacterListItem, CharacterListType, CharacterAudio, DictationHint
from sqlalchemy.orm import Session
import re
from app.utils.audio_generator import AudioGenerator

def parse_character_line(line):
    """解析字符行，格式: 字(pinyin):提示词"""
    match = re.match(r'(\w)([\w\d]+):(.+)', line)
    if not match:
        return None
    char, pinyin, hint = match.groups()
    return {
        'character': char,
        'pinyin': pinyin,
        'hint': hint
    }

def import_characters(file_path, grade, semester, char_type='识字'):
    """
    导入字表
    :param file_path: 文件路径
    :param grade: 年级
    :param semester: 学期
    :param char_type: 字表类型（'识字'或'写字'）
    """
    app = create_app()
    with app.app_context():
        # 获取或创建字表类型
        list_type = CharacterListType.query.filter_by(
            grade=grade,
            semester=semester,
            type=char_type
        ).first()
        
        if not list_type:
            list_type = CharacterListType(grade=grade, semester=semester, type=char_type)
            db.session.add(list_type)
            db.session.commit()
        
        # 创建字表
        char_list = CharacterList(type_id=list_type.id)
        db.session.add(char_list)
        db.session.commit()
        
        current_unit = None
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('[Unit'):
                    current_unit = int(line[5:-1])
                    continue
                    
                # 解析字和提示词
                parts = line.split(':')
                if len(parts) != 2:
                    continue
                    
                char_with_pinyin, hint = parts
                # 提取汉字（去除拼音部分）
                char = re.match(r'([^\(]+)', char_with_pinyin).group(1).strip()
                
                # 创建或获取字符
                character = Character.query.filter_by(character=char).first()
                if not character:
                    character = Character(character=char)
                    db.session.add(character)
                    db.session.commit()
                
                # 创建字表项
                list_item = CharacterListItem(
                    list_id=char_list.id,
                    character_id=character.id,
                    unit=current_unit
                )
                db.session.add(list_item)
                
                # 添加提示词
                if hint:
                    hint_obj = DictationHint(
                        character_id=character.id,
                        hint_word=hint,
                        type=char_type
                    )
                    db.session.add(hint_obj)
                
        db.session.commit()

if __name__ == '__main__':
    # 导入识字表
    import_characters('data/yuwen/renjiaoban/grade_4_1/shizibiao.txt', grade=4, semester=1, char_type='识字')
    # 导入写字表
    import_characters('data/yuwen/renjiaoban/grade_4_1/xiezibiao.txt', grade=4, semester=1, char_type='写字') 
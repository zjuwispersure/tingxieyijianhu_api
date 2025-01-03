import os
import sys
from pypinyin import pinyin, Style
import re
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.models import db
from app.models.yuwen import YuwenItem

# 获取 OSS 配置
OSS_CDN_DOMAIN = os.getenv('OSS_CDN_DOMAIN')

def get_pinyin(text):
    """获取拼音"""
    return ' '.join([p[0] for p in pinyin(text, style=Style.TONE3)])

def parse_unit_text(unit_text):
    """解析单元标记
    Args:
        unit_text: 单元标记文本，如 [Unit 1] 或 [语文园地一]
    Returns:
        str: 单元标记，如 'Unit 1' 或 '语文园地一'
    """
    # 移除方括号并返回内容
    return unit_text.strip('[]')

def import_items(file_path, item_type, audio_dir, book_version, grade, semester):
    """导入字/词数据
    Args:
        file_path: 数据文件路径
        item_type: 类型（识字/写字/词语）
        audio_dir: OSS 音频目录路径
        book_version: 教材版本
        grade: 年级
        semester: 学期
    """
    print(f"Importing {item_type} for {book_version} grade {grade} semester {semester}")
    print(f"Audio OSS path: {audio_dir}")
    
    current_unit = None
    items_to_add = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 处理单元标记
            if line.startswith('['):
                current_unit = parse_unit_text(line)
                print(f"Processing {current_unit}")
                continue
            
            if current_unit is None:
                print(f"Warning: No unit specified for line: {line}")
                continue
            
            if item_type == '词语':
                # 词语表的每行可能包含多个词语，用空格分隔
                for word in line.split():
                    word = word.strip()
                    if not word:
                        continue
                    
                    pinyin = get_pinyin(word)  # 词语用生成的拼音
                    hint = word  # 词语的提示词就是词语本身
                    
                    items_to_add.append({
                        'word': word,
                        'pinyin': pinyin,
                        'hint': hint,
                        'unit': current_unit
                    })
            else:
                # 处理识字表和写字表的行，格式：字(pin1yin1):提示词
                parts = line.split(':')
                if len(parts) != 2:
                    print(f"Warning: Invalid format for line: {line}")
                    continue
                
                char_with_pinyin, hint = parts
                # 提取汉字和拼音
                match = re.match(r'([^\(]+)\(([^\)]+)\)', char_with_pinyin)
                if not match:
                    print(f"Warning: Cannot parse character and pinyin: {char_with_pinyin}")
                    continue
                
                word = match.group(1).strip()
                pinyin = match.group(2).strip()  # 使用文件中的拼音
                hint = hint.strip()
                
                items_to_add.append({
                    'word': word,
                    'pinyin': pinyin,
                    'hint': hint,
                    'unit': current_unit
                })
    
    # 批量创建记录
    for item_data in items_to_add:
        word = item_data['word']
        # 生成音频 URL
        audio_url = f"{audio_dir}/{word}.mp3"
        print(f"Audio URL: {audio_url}")
        
        # 创建数据记录
        item = YuwenItem(
            word=word,
            type=item_type,
            book_version=book_version,
            grade=grade,
            semester=semester,
            unit=item_data['unit'],
            pinyin=item_data['pinyin'],
            hint=item_data['hint'],
            audio_url=audio_url
        )
        db.session.add(item)
    
    db.session.commit()
    print(f"{item_type} imported successfully")

def main():
    # 从环境变量获取基础路径
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    OSS_CDN_DOMAIN = os.getenv('OSS_CDN_DOMAIN')
    
    # 导入参数
    book_version = 'renjiaoban'
    grade = 4
    semester = 1
    subject = 'yuwen'
   
    
    base_path = os.path.join(
        DATA_DIR,
        subject,
        book_version,
        f"grade_{grade}_{semester}"
    )
    oss_base_path = os.path.join(
        OSS_CDN_DOMAIN,
        'data',
        subject,
        book_version,
        f"grade_{grade}_{semester}"
    ) 
    
    # 音频目录
    audio_dirs = {
        '识字': f"{oss_base_path}/audio_识字",
        '写字': f"{oss_base_path}/audio_写字",
        '词语': f"{oss_base_path}/audio_词语"
    }
    
    app = create_app()
    with app.app_context():
        # 导入识字表
        shizi_path = os.path.join(base_path, "shizibiao.txt")
        if os.path.exists(shizi_path):
            import_items(shizi_path, '识字', audio_dirs['识字'], 
                       book_version, grade, semester)
        
        # 导入写字表
        xiezi_path = os.path.join(base_path, "xiezibiao.txt")
        if os.path.exists(xiezi_path):
            import_items(xiezi_path, '写字', audio_dirs['写字'],
                       book_version, grade, semester)
        
        # 导入词语表
        ciyu_path = os.path.join(base_path, "ciyubiao.txt")
        if os.path.exists(ciyu_path):
            import_items(ciyu_path, '词语', audio_dirs['词语'],
                       book_version, grade, semester)

if __name__ == '__main__':
    main() 
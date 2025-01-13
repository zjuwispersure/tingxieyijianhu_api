import os
import sys
from pypinyin import pinyin, Style
import re
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.models import db
from app.models.yuwen_item import YuwenItem

def get_pinyin(text):
    """获取拼音"""
    return ' '.join([p[0] for p in pinyin(text, style=Style.TONE3)])

def parse_unit_and_lesson(text):
    """解析单元和课文信息
    Args:
        text: 标记文本，如 [第一单元] 或 [1.观潮] 或 [语文园地]
    Returns:
        tuple: (unit_number, lesson_number, lesson_name)
    """
    text = text.strip('[]')
    
    # 处理单元标记
    if text.startswith('第') and text.endswith('单元'):
        unit_number = text[1:-2]  # 移除"第"和"单元"
        # 将中文数字转换为阿拉伯数字
        chinese_numbers = {'一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8}
        return chinese_numbers.get(unit_number), None, None
        
    # 处理语文园地
    if text.startswith('语文园地'):
        # 将语文园地作为特殊的课文，lesson_number 使用 99 表示
        return None, 99, text
        
    # 处理普通课文标记
    if '.' in text:
        lesson_num, lesson_name = text.split('.', 1)
        return None, int(lesson_num), lesson_name
        
    return None, None, None

def import_items(file_path, item_type, audio_dir, grade, semester, textbook_version='renjiaoban'):
    """导入语文条目"""
    try:
        # 先删除对应年级、学期、教材版本的数据
        YuwenItem.query.filter_by(
            grade=grade,
            semester=semester,
            textbook_version=textbook_version,
            type=item_type  # 只删除相同类型的数据
        ).delete()
        db.session.commit()
        
        print(f"Importing {item_type} from {file_path}")
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            current_unit = None
            current_lesson = None
            lesson_name = None
            
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                # 处理单元信息
                if line.startswith('Unit'):
                    current_unit = int(line.split()[1])
                    print(f"Processing Unit {current_unit}")
                    continue
                    
                # 处理课文信息
                if line.startswith('Lesson'):
                    current_lesson = int(line.split()[1])
                    lesson_name = ' '.join(line.split()[2:])
                    print(f"Processing Lesson {lesson_name}")
                    continue
                    
                # 处理语文园地
                if line.startswith('语文园地'):
                    current_lesson = 0
                    lesson_name = line
                    print(f"Processing {lesson_name}")
                    continue
                    
                # 处理词语
                parts = line.split('\t')
                if len(parts) >= 2:
                    word, pinyin = parts[:2]
                    
                    # 生成音频URL
                    audio_url = f"https://review-audios.oss-cn-shanghai.aliyuncs.com/audio/yuwen/{textbook_version}/grade_{grade}_{semester}/{item_type}/{word}.mp3"
                    
                    # 创建新条目
                    item = create_yuwen_item(
                        word=word,
                        pinyin=pinyin,
                        item_type=item_type,
                        unit=current_unit,
                        lesson=current_lesson,
                        lesson_name=lesson_name,
                        grade=grade,
                        semester=semester,
                        textbook_version=textbook_version,
                        audio_url=audio_url
                    )
                    db.session.add(item)
            
            # 提交所有更改
            db.session.commit()
            
    except Exception as e:
        db.session.rollback()
        print(f"Error importing data: {str(e)}")
        raise

def main():
    # 配置参数
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    OSS_CDN_DOMAIN = os.getenv('OSS_CDN_DOMAIN')
    
    book_version = 'renjiaoban'
    grade = 4
    semester = 1
    subject = 'yuwen'
    
    base_path = f"{DATA_DIR}/{subject}/{book_version}/grade_{grade}_{semester}"
    audio_base = f"{OSS_CDN_DOMAIN}/audio/{subject}/{book_version}/grade_{grade}_{semester}"
    
    app = create_app()
    with app.app_context():
        # 导入数据
        for item_type, filename in [
            ('识字', 'shizibiao.txt'),
            ('写字', 'xiezibiao.txt'),
            ('词语', 'ciyubiao.txt')
        ]:
            file_path = os.path.join(base_path, filename)
            if os.path.exists(file_path):
                # 清空对应类型的现有数据
                YuwenItem.query.filter_by(
                    grade=grade,
                    semester=semester,
                    textbook_version=book_version,
                    type=item_type  # 添加类型过滤
                ).delete()
                db.session.commit()  # 提交删除操作
                
                audio_dir = f"{audio_base}/{item_type}"
                import_items(file_path, item_type, audio_dir, grade, semester, book_version)

if __name__ == '__main__':
    main() 
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import re
from app.utils.audio_generator import YuwenAudioGenerator

async def generate_audio_for_file(input_file, audio_gen):
    """
    从文本文件批量生成音频
    :param input_file: 输入文件路径 (shizibiao.txt)
    :param audio_gen: AudioGenerator实例
    """
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Found {len(lines)} lines in file")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('['):
                continue
                
            print(f"Processing line {line_num}: {line}")
            # 解析行内容，格式: 盐(yan2):食盐
            match = re.match(r'([^\(]+)\(([^\)]+)\):(.+)', line)
            if not match:
                print(f"No match for line: {line}")
                continue
                
            char, pinyin, hint_word = match.groups()
            char = char.strip()
            hint_word = hint_word.strip()
            print(f"Extracted: char={char}, pinyin={pinyin}, hint={hint_word}")
            
            try:
                audio_path = await audio_gen.generate_audio(char, hint_word)
                print(f"Generated audio for {char}: {audio_path}")
            except Exception as e:
                print(f"Error generating audio for {char}: {str(e)}") 

async def generate_audio_for_ciyu(input_file, audio_gen):
    """
    从词语表文件批量生成音频
    :param input_file: 输入文件路径 (ciyubiao.txt)
    :param audio_gen: AudioGenerator实例
    """
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Found {len(lines)} lines in file")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('['):
                continue
                
            print(f"Processing line {line_num}: {line}")
            # 每行可能包含多个词语，用空格分隔
            for word in line.split():
                try:
                    audio_path = await audio_gen.generate_audio(word, None)
                    print(f"Generated audio for {word}: {audio_path}")
                except Exception as e:
                    print(f"Error generating audio for {word}: {str(e)}") 
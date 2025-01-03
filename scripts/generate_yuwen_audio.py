import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.utils.audio_generator import YuwenAudioGenerator
from scripts.batch_generate_audio import generate_audio_for_ciyu, generate_audio_for_file

async def main():
    grade = 4 
    semester = 1
    book_version = 'renjiaoban'

    """生成词语表音频"""
    audio_gen = YuwenAudioGenerator(grade=grade, semester=semester, char_type='词语', book_version=book_version)
    await generate_audio_for_ciyu('data/yuwen/renjiaoban/grade_4_1/ciyubiao.txt', audio_gen)

    """生成识字表音频"""
    audio_gen = YuwenAudioGenerator(grade=grade, semester=semester, char_type='识字', book_version=book_version)
    await generate_audio_for_file('data/yuwen/renjiaoban/grade_4_1/shizibiao.txt', audio_gen)

    """生成写字表音频"""
    audio_gen = YuwenAudioGenerator(grade=grade, semester=semester, char_type='写字', book_version=book_version)
    await generate_audio_for_file('data/yuwen/renjiaoban/grade_4_1/xiezibiao.txt', audio_gen)

if __name__ == "__main__":
    print("Starting 词语表 audio generation...")
    asyncio.run(main()) 
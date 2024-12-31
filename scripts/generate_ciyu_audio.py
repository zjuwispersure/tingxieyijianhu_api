import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.utils.audio_generator import AudioGenerator
from scripts.batch_generate_audio import generate_audio_for_ciyu

async def main():
    """生成词语表音频"""
    audio_gen = AudioGenerator(grade=4, semester=1, char_type='词语')
    await generate_audio_for_ciyu('data/yuwen/renjiaoban/grade_4_1/ciyubiao.txt', audio_gen)

if __name__ == "__main__":
    print("Starting 词语表 audio generation...")
    asyncio.run(main()) 
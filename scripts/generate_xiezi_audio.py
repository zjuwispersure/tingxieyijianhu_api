import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.utils.audio_generator import AudioGenerator
from scripts.batch_generate_audio import generate_audio_for_file

async def main():
    """生成写字表音频"""
    audio_gen = AudioGenerator(grade=4, semester=1, char_type='写字')
    await generate_audio_for_file('data/yuwen/renjiaoban/grade_4_1/xiezibiao.txt', audio_gen)

if __name__ == "__main__":
    print("Starting 写字表 audio generation...")
    asyncio.run(main()) 
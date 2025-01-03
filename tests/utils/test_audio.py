import os
import sys
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
from app.utils.audio_generator import YuwenAudioGenerator

async def test_audio():
    # 指定年级和学期
    generator = YuwenAudioGenerator(grade=4, semester=1)
    
    # 测试单个字的生成
    test_char = "盐"
    test_hint = "咸味的盐"
    
    try:
        audio_path = await generator.generate_audio(test_char, test_hint)
        print(f"Successfully generated audio for {test_char}")
        print(f"Audio file saved at: {audio_path}")
    except Exception as e:
        print(f"Error generating audio: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_audio()) 
import pytest
import os
from app.utils.audio_generator import YuwenAudioGenerator

@pytest.mark.asyncio
async def test_audio_generation():
    generator = YuwenAudioGenerator(grade=4, semester=1)
    
    test_char = "盐"
    test_hint = "咸味的盐"
    
    audio_path = await generator.generate_audio(test_char, test_hint)
    
    # 验证文件是否生成
    assert os.path.exists(audio_path)
    # 验证文件路径是否正确
    expected_path = os.path.join('data/yuwen/renjiaoban/grade_4_1/audio', f'{test_char}.mp3')
    assert audio_path == expected_path

@pytest.mark.asyncio
async def test_audio_cache():
    """测试音频文件缓存功能"""
    generator = YuwenAudioGenerator(grade=4, semester=1)
    
    test_char = "盐"
    test_hint = "咸味的盐"
    
    # 第一次生成
    path1 = await generator.generate_audio(test_char, test_hint)
    # 第二次应该直接返回缓存
    path2 = await generator.generate_audio(test_char, test_hint)
    
    assert path1 == path2 
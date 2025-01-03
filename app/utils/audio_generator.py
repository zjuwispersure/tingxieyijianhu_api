import edge_tts
import os

class YuwenAudioGenerator:
    def __init__(self, grade=4, semester=1, char_type='识字', book_version='renjiaoban'):
        # 定义音频文件的基础目录
        self.base_dir = 'data/yuwen/'+ book_version
        self.grade_dir = f'grade_{grade}_{semester}'
        # 根据字表类型区分音频目录
        self.relative_audio_dir = os.path.join(self.base_dir, self.grade_dir, f'audio_{char_type}')
        
        # 确保目录存在
        os.makedirs(self.relative_audio_dir, exist_ok=True)
        
        # 参考文档：https://pypi.org/project/edge-tts/
        # 设置中文语音
        self.voice = "zh-CN-XiaoxiaoNeural"
        # 设置语速 (-50% 到 +50%)
        self.rate = "-20%"  # 降低20%的语速
        
    async def generate_audio(self, character, hint_word):
        """
        生成单个汉字或词语的语音文件
        :param character: 汉字或词语
        :param hint_word: 提示词，可以为None
        :return: 音频文件的相对路径
        """
        # 生成音频文件路径
        audio_filename = f'{character}.mp3'
        relative_path = os.path.join(self.relative_audio_dir, audio_filename)
        
        # 如果文件已存在，直接返回相对路径
        if os.path.exists(relative_path):
            return relative_path
            
        # 生成文本
        text = hint_word and f"{hint_word}，的{character}" or character
        
        # 生成语音文件，设置语速
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
        await communicate.save(relative_path)
                
        return relative_path 
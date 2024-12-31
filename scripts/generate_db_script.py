import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_db_script():
    """生成数据库操作脚本"""
    script_content = """#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "开始初始化数据库..."

# 创建数据库目录
mkdir -p instance

# 初始化数据库
echo "创建数据库表..."
flask db upgrade

# 导入基础数据
echo "导入字表数据..."
python scripts/import_characters.py

# 生成音频文件
echo "生成识字表音频..."
python scripts/generate_shizi_audio.py

echo "生成写字表音频..."
python scripts/generate_xiezi_audio.py

echo "生成词语表音频..."
python scripts/generate_ciyu_audio.py

echo "数据库初始化完成！"
"""

    # 写入脚本文件
    script_path = 'scripts/init_db.sh'
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod(script_path, 0o755)
    
    print(f"数据库初始化脚本已生成: {script_path}")
    print("在服务器上执行以下命令:")
    print("1. cd /path/to/project")
    print("2. ./scripts/init_db.sh")

if __name__ == '__main__':
    generate_db_script() 
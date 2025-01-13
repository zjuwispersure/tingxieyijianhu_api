import os
import sys
from flask import Flask

# 添加项目根目录到 Python 路径
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

print("Current directory:", current_dir)
print("Python path:", sys.path)

try:
    from app import create_app
    app = create_app()
    
    # 添加一个简单的路由用于测试
    @app.route('/test')
    def test():
        return 'Hello, World!'
        
    # 确保 Flask CLI 可以找到应用实例
    application = app
except Exception as e:
    print("Error during app initialization:", str(e))
    raise

if __name__ == '__main__':
    app.run() 
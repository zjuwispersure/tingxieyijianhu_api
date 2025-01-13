from flask import Blueprint

# 创建蓝图
dictation_bp = Blueprint('dictation', __name__)

# 导入路由 - 放在最后避免循环导入
from . import routes 
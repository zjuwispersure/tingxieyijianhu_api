from flask import Blueprint

# 创建蓝图
dictation_bp = Blueprint('dictation', __name__)
dictation_config_bp = Blueprint('dictation_config', __name__)

# 导入路由 - 放在最后避免循环导入
from . import dicattion_routes 
from . import config_routes
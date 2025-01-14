from flask import Blueprint

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# 导入路由 - 放在最后避免循环导入
from . import auth_routes
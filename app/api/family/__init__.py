from flask import Blueprint

# 创建蓝图
family_bp = Blueprint('family', __name__)

# 导入路由 - 放在最后避免循环导入
from . import children_routes
from . import family_routes
"""
错误码定义

格式说明:
- 1xxx: 参数相关错误
- 2xxx: 认证/授权错误
- 3xxx: 资源错误
- 4xxx: 业务逻辑错误
- 5xxx: 系统错误
"""

# 参数相关错误 (1xxx)
INVALID_REQUEST_FORMAT = 1001  # 无效的请求格式
MISSING_REQUIRED_PARAM = 1002  # 缺少必要参数
INVALID_PARAM_TYPE = 1003     # 参数类型错误
INVALID_PARAM_VALUE = 1004    # 参数值无效

# 认证/授权错误 (2xxx)
UNAUTHORIZED = 2001           # 未登录
INVALID_TOKEN = 2002         # token无效
PERMISSION_DENIED = 2003     # 权限不足
LOGIN_FAILED = 2004          # 登录失败
INVALID_WX_CODE = 2005       # 无效的微信登录码
USER_NOT_FOUND = 2004  # 用户不存在


# 资源错误 (3xxx)
RESOURCE_NOT_FOUND = 3001      # 资源不存在
RESOURCE_ALREADY_EXISTS = 3002  # 资源已存在
RESOURCE_STATUS_ERROR = 3003    # 资源状态错误

# 子资源错误 (31xx)
CHILD_NOT_FOUND = 3101         # 找不到该孩子
CONFIG_NOT_FOUND = 3102        # 找不到配置

# 业务逻辑错误 (4xxx)
OPERATION_NOT_ALLOWED = 4001    # 操作不允许
STATUS_CONFLICT = 4002         # 状态冲突
INVALID_WX_CODE = 4002       # 无效的微信登录码
INVALID_PARAMETER = 4004  # 无效的参数

# 数据重复错误 (41xx)
DUPLICATE_NICKNAME = 4101      # 昵称重复
DUPLICATE_CHILD = 4102         # 孩子重复
CONFIG_ALREADY_EXISTS = 4103   # 配置已存在
DUPLICATE_RECORD = 4003
SESSION_NOT_FOUND = 4004  # 听写会话不存在

# 系统错误 (5xxx)
INTERNAL_ERROR = 5001        # 内部错误
DATABASE_ERROR = 5002        # 数据库错误
SERVICE_BUSY = 5003          # 服务繁忙
EXTERNAL_SERVICE_ERROR = 5003  # 外部服务错误
WX_API_ERROR = 5101          # 微信接口错误

# 错误信息映射
ERROR_MESSAGES = {
    INVALID_REQUEST_FORMAT: '无效的请求数据格式，需要 JSON 格式',
    MISSING_REQUIRED_PARAM: '缺少必要参数: {}',
    INVALID_PARAM_TYPE: '参数类型错误: {}',
    INVALID_PARAM_VALUE: '参数值无效: {}',
    
    UNAUTHORIZED: '请先登录',
    INVALID_TOKEN: '无效的登录凭证',
    PERMISSION_DENIED: '没有权限执行此操作',
    LOGIN_FAILED: '登录失败: {}',
    
    RESOURCE_NOT_FOUND: '资源不存在',
    RESOURCE_ALREADY_EXISTS: '资源已存在',
    RESOURCE_STATUS_ERROR: '资源状态错误',
    CHILD_NOT_FOUND: '找不到该孩子',
    CONFIG_NOT_FOUND: '找不到配置',
    DUPLICATE_CHILD: '该孩子已存在',
    
    OPERATION_NOT_ALLOWED: '不允许的操作',
    STATUS_CONFLICT: '状态冲突',
    DUPLICATE_NICKNAME: '昵称已存在',
    CONFIG_ALREADY_EXISTS: '配置已存在',
    
    INTERNAL_ERROR: '系统内部错误',
    DATABASE_ERROR: '数据库错误',
    EXTERNAL_SERVICE_ERROR: '外部服务错误',
    WX_API_ERROR: '微信接口错误: {}',
    INVALID_WX_CODE: '无效的微信登录码',
    USER_NOT_FOUND: '用户不存在',
    INVALID_PARAMETER: '无效的参数: {}',
    DUPLICATE_RECORD: '记录已存在',
    SESSION_NOT_FOUND: '听写会话不存在',
}

def get_error_message(code, *args):
    """获取错误信息
    
    Args:
        code: 错误码
        *args: 格式化参数
    
    Returns:
        str: 格式化后的错误信息
    """
    message = ERROR_MESSAGES.get(code, '未知错误')
    if args:
        try:
            return message.format(*args)
        except:
            return message
    return message 
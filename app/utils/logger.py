import logging
import pytz
from datetime import datetime
from functools import wraps

# 设置北京时区
beijing_tz = pytz.timezone('Asia/Shanghai')

class BeijingFormatter(logging.Formatter):
    """自定义日志格式化器，使用北京时间"""
    def formatTime(self, record, datefmt=None):
        utc_dt = datetime.fromtimestamp(record.created, pytz.UTC)
        beijing_dt = utc_dt.astimezone(beijing_tz)
        return beijing_dt.strftime(datefmt or '%Y-%m-%d %H:%M:%S')

# 配置日志
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

# 创建处理器并设置格式化器
handler = logging.StreamHandler()
handler.setFormatter(BeijingFormatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    '%Y-%m-%d %H:%M:%S'
))
logger.addHandler(handler)

# 确保 logger 有所有日志级别的方法
def error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    logger.info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    logger.warning(msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    logger.critical(msg, *args, **kwargs)

# API调用日志装饰器
def log_api_call(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        info(f"API调用: {f.__name__}")
        return f(*args, **kwargs)
    return decorated_function
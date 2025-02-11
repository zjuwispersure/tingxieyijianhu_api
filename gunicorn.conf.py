import os
import logging

# 工作进程数
workers = 4
# 绑定地址
bind = '0.0.0.0:5000'

# 日志配置
accesslog = '-'  # '-' 表示输出到标准输出
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info')

# 自定义访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# 日志格式说明：
# %(h)s: 远程地址
# %(l)s: '-'
# %(u)s: 用户名
# %(t)s: 时间
# %(r)s: 请求行
# %(s)s: 状态码
# %(b)s: 响应大小
# %(f)s: referer
# %(a)s: user agent
# %(L)s: 请求处理时间（毫秒）

# 可以选择隐藏某些敏感信息
access_log_format = '%(t)s "%(r)s" %(s)s %(b)s %(L)s ms'  # 只保留关键信息

# 日志处理器
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'generic': {
            'format': '%(asctime)s [%(process)d] [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'class': 'logging.Formatter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'gunicorn.error': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'gunicorn.access': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        }
    }
}

# 是否捕获输出
capture_output = True
# 是否打印访问日志
enable_stdio_inheritance = True 
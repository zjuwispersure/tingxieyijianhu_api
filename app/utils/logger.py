import json
import logging
from datetime import datetime
from flask import request, g, current_app

def setup_logger():
    """设置JSON格式的日志记录器"""
    logger = logging.getLogger('yuwen')
    logger.setLevel(logging.INFO)
    
    # 创建文件处理器
    handler = logging.FileHandler('logs/yuwen.log')
    handler.setLevel(logging.INFO)
    
    # 设置JSON格式
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def log_message(message_dict):
    """
    记录JSON格式的日志
    :param message_dict: 要记录的消息字典
    """
    logger = logging.getLogger('yuwen')
    
    # 添加基础信息
    base_info = {
        'timestamp': datetime.utcnow().isoformat(),
        'ip': request.remote_addr if request else None,
        'user_id': g.user.id if hasattr(g, 'user') else None,
        'endpoint': request.endpoint if request else None,
        'environment': current_app.config['ENV'] if current_app else 'unknown'
    }
    
    # 合并消息
    log_data = {**base_info, **message_dict}
    
    # 记录JSON格式的日志
    logger.info(json.dumps(log_data))
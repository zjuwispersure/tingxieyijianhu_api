from functools import wraps
from flask import current_app
import redis
import json
from datetime import datetime

class RedisCache:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        redis_url = app.config.get('REDIS_URL', 'redis://redis:6379/0')
        self.redis = redis.from_url(redis_url)
        
    def key_prefix(self, prefix):
        """生成带前缀的缓存键装饰器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 生成缓存键
                key_parts = [prefix]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
                
                # 尝试获取缓存
                cached = self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
                
                # 执行原函数
                result = f(*args, **kwargs)
                
                # 缓存结果
                self.redis.setex(
                    cache_key,
                    current_app.config.get('CACHE_TIMEOUT', 300),  # 默认5分钟
                    json.dumps(result)
                )
                
                return result
            return decorated_function
        return decorator
    
    def invalidate_prefix(self, prefix):
        """使指定前缀的所有缓存失效"""
        pattern = f"{prefix}*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)

# 创建缓存实例
cache = RedisCache() 
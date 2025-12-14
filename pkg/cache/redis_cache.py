# -*- coding: utf-8 -*-
"""
Redis缓存实现
使用Redis作为缓存后端，支持分布式缓存
"""

import pickle
from typing import Any, List

from redis import Redis

import config
from .abs_cache import AbstractCache


class RedisCache(AbstractCache):
    """
    Redis缓存实现
    使用Redis作为缓存后端，支持分布式部署
    
    设计思路：
    1. 使用Redis存储缓存数据
    2. 使用pickle序列化/反序列化数据
    3. 支持过期时间设置
    4. 支持模式匹配查找键
    """
    
    def __init__(self) -> None:
        """
        初始化Redis缓存
        连接Redis服务器
        """
        # 连接redis，返回redis客户端
        self._redis_client = self._connect_redis()

    @staticmethod
    def _connect_redis() -> Redis:
        """
        连接Redis，返回Redis客户端
        
        Returns:
            Redis: Redis客户端实例
        """
        return Redis(
            host=config.REDIS_DB_HOST,
            port=config.REDIS_DB_PORT,
            db=config.REDIS_DB_NUM,
            password=config.REDIS_DB_PWD,
            decode_responses=False  # 不自动解码，使用pickle序列化
        )

    def get(self, key: str) -> Any:
        """
        从缓存中获取键的值，并反序列化
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值，如果不存在返回None
        """
        value = self._redis_client.get(key)
        if value is None:
            return None
        # 使用pickle反序列化
        return pickle.loads(value)

    def set(self, key: str, value: Any, expire_time: int) -> None:
        """
        将键的值设置到缓存中，并序列化
        
        Args:
            key: 缓存键
            value: 缓存值
            expire_time: 过期时间（秒）
        """
        # 使用pickle序列化，并设置过期时间
        self._redis_client.set(key, pickle.dumps(value), ex=expire_time)

    def delete(self, key: str) -> None:
        """
        删除缓存键
        
        Args:
            key: 缓存键
        """
        self._redis_client.delete(key)

    def keys(self, pattern: str) -> List[str]:
        """
        获取所有符合pattern的键
        
        Args:
            pattern: 匹配模式，支持Redis通配符（*、?、[]等）
            
        Returns:
            List[str]: 匹配的键列表
        """
        # Redis返回的是bytes类型，需要解码
        return [key.decode() for key in self._redis_client.keys(pattern)]

    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间（秒）
        
        Args:
            key: 缓存键
            
        Returns:
            int: 剩余生存时间（秒），-1表示永不过期，-2表示键不存在
        """
        return self._redis_client.ttl(key)

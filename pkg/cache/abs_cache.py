# -*- coding: utf-8 -*-
"""
缓存抽象基类
定义缓存系统的统一接口
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional


class AbstractCache(ABC):
    """
    缓存抽象基类
    所有缓存实现都必须继承此类并实现其抽象方法
    
    设计思路：
    1. 使用抽象基类确保所有缓存实现都有统一的接口
    2. 支持键值对的存储、获取、删除
    3. 支持过期时间设置
    4. 支持模式匹配查找键
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        从缓存中获取键的值
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值，如果不存在或已过期返回None
        """
        raise NotImplementedError("子类必须实现 get 方法")

    @abstractmethod
    def set(self, key: str, value: Any, expire_time: int) -> None:
        """
        将键的值设置到缓存中
        
        Args:
            key: 缓存键
            value: 缓存值
            expire_time: 过期时间（秒）
        """
        raise NotImplementedError("子类必须实现 set 方法")

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        删除缓存键
        
        Args:
            key: 缓存键
        """
        raise NotImplementedError("子类必须实现 delete 方法")

    @abstractmethod
    def keys(self, pattern: str) -> List[str]:
        """
        获取所有符合pattern的键
        
        Args:
            pattern: 匹配模式（支持通配符）
            
        Returns:
            List[str]: 匹配的键列表
        """
        raise NotImplementedError("子类必须实现 keys 方法")

    @abstractmethod
    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间（秒）
        
        Args:
            key: 缓存键
            
        Returns:
            int: 剩余生存时间（秒），-1表示永不过期，-2表示键不存在
        """
        raise NotImplementedError("子类必须实现 ttl 方法")

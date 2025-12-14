# -*- coding: utf-8 -*-
"""
本地缓存实现
使用内存字典实现的带过期时间的本地缓存
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

from .abs_cache import AbstractCache


class ExpiringLocalCache(AbstractCache):
    """
    带过期时间的本地缓存
    使用内存字典存储数据，支持自动过期清理
    
    设计思路：
    1. 使用字典存储键值对，值包含数据和过期时间
    2. 后台任务定期清理过期数据
    3. 获取数据时检查是否过期
    """
    
    def __init__(self, cron_interval: int = 10):
        """
        初始化本地缓存
        
        Args:
            cron_interval: 定时清理缓存的时间间隔（秒），默认10秒
        """
        self._cron_interval = cron_interval
        # 缓存容器：key -> (value, expire_time)
        self._cache_container: Dict[str, Tuple[Any, float]] = {}
        self._cron_task: Optional[asyncio.Task] = None
        self._loop = asyncio.get_event_loop()
        # 开启定时清理任务
        self._schedule_clear()

    def __del__(self):
        """
        析构函数，清理定时任务
        """
        self.stop()

    def stop(self):
        """
        停止定时清理任务
        """
        if self._cron_task is not None:
            self._cron_task.cancel()
            try:
                self._loop.run_until_complete(self._cron_task)
            except asyncio.CancelledError:
                pass
            self._cron_task = None

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存中获取键的值
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值，如果不存在或已过期返回None
        """
        value, expire_time = self._cache_container.get(key, (None, 0))
        if value is None:
            return None

        # 如果键已过期，则删除键并返回None
        if expire_time < time.time():
            del self._cache_container[key]
            return None

        return value

    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间（秒）
        
        Args:
            key: 缓存键
            
        Returns:
            int: 剩余生存时间（秒），-2表示键不存在或已过期
        """
        value, expire_time = self._cache_container.get(key, (None, 0))
        if value is None:
            return -2

        # 如果键已过期，则删除键并返回-2
        if expire_time < time.time():
            del self._cache_container[key]
            return -2

        return int(expire_time - time.time())

    def set(self, key: str, value: Any, expire_time: int) -> None:
        """
        将键的值设置到缓存中
        
        Args:
            key: 缓存键
            value: 缓存值
            expire_time: 过期时间（秒）
        """
        # 存储值和过期时间（当前时间 + 过期时间）
        self._cache_container[key] = (value, time.time() + expire_time)

    def delete(self, key: str) -> None:
        """
        删除缓存键
        
        Args:
            key: 缓存键
        """
        if key in self._cache_container:
            del self._cache_container[key]

    def keys(self, pattern: str) -> List[str]:
        """
        获取所有符合pattern的键
        
        Args:
            pattern: 匹配模式，支持'*'通配符
            
        Returns:
            List[str]: 匹配的键列表
        """
        if pattern == '*':
            return list(self._cache_container.keys())

        # 本地缓存通配符暂时将*替换为空
        if '*' in pattern:
            pattern = pattern.replace('*', '')

        return [key for key in self._cache_container.keys() if pattern in key]

    def _schedule_clear(self):
        """
        开启定时清理任务
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self._cron_task = loop.create_task(self._start_clear_cron())

    def _clear(self):
        """
        根据过期时间清理缓存
        删除所有已过期的键
        """
        current_time = time.time()
        # 收集需要删除的键
        keys_to_delete = [
            key for key, (value, expire_time) in self._cache_container.items()
            if expire_time < current_time
        ]
        # 删除过期的键
        for key in keys_to_delete:
            del self._cache_container[key]

    async def _start_clear_cron(self):
        """
        开启定时清理任务（异步）
        每隔指定时间清理一次过期数据
        """
        while True:
            self._clear()
            await asyncio.sleep(self._cron_interval)

# -*- coding: utf-8 -*-
"""
缓存工厂类
根据配置创建不同类型的缓存实例（本地缓存或Redis缓存）
"""


class CacheFactory:
    """
    缓存工厂类
    使用工厂模式创建不同类型的缓存实例
    
    设计思路：
    1. 根据配置的缓存类型创建相应的缓存实例
    2. 支持本地缓存（memory）和Redis缓存（redis）
    3. 统一接口，便于切换缓存类型
    """
    
    @staticmethod
    def create_cache(cache_type: str, *args, **kwargs):
        """
        创建缓存对象
        
        Args:
            cache_type: 缓存类型，'memory'（本地缓存）或 'redis'（Redis缓存）
            *args: 位置参数，传递给缓存构造函数
            **kwargs: 关键字参数，传递给缓存构造函数
            
        Returns:
            AbstractCache: 缓存实例
            
        Raises:
            ValueError: 如果缓存类型未知
        """
        if cache_type == 'memory':
            # 导入本地缓存类
            from .local_cache import ExpiringLocalCache
            return ExpiringLocalCache(*args, **kwargs)
        elif cache_type == 'redis':
            # 导入Redis缓存类
            from .redis_cache import RedisCache
            return RedisCache()
        else:
            raise ValueError(f'Unknown cache type: {cache_type}')

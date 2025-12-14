# -*- coding: utf-8 -*-
"""
缓存模块
提供本地缓存和Redis缓存实现
"""

from .cache_factory import CacheFactory
from .abs_cache import AbstractCache

__all__ = ['CacheFactory', 'AbstractCache']

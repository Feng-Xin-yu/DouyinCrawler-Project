# -*- coding: utf-8 -*-
"""
数据库配置模块
配置Redis的连接信息（用于缓存）
"""

import os

# ==================== Redis配置 ====================
# Redis缓存连接配置
# 可以通过环境变量设置，如果没有设置则使用默认值
REDIS_DB_HOST = os.getenv("REDIS_DB_HOST", "127.0.0.1")
REDIS_DB_PWD = os.getenv("REDIS_DB_PWD", "123456")
REDIS_DB_PORT = os.getenv("REDIS_DB_PORT", 6379)
REDIS_DB_NUM = os.getenv("REDIS_DB_NUM", 0)

# ==================== 缓存类型配置 ====================
# 缓存类型：redis 或 memory（内存）
# 推荐使用 redis，因为：
# 1. 程序重启后缓存不会丢失
# 2. 不会浪费代理IP（代理IP信息会缓存在redis中）
# 3. 支持多进程/多机器共享缓存
CACHE_TYPE_REDIS = "redis"
CACHE_TYPE_MEMORY = "memory"
USE_CACHE_TYPE = CACHE_TYPE_REDIS

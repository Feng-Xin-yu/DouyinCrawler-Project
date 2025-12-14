# -*- coding: utf-8 -*-
"""
基础抽象类模块
定义爬虫、存储、API客户端的抽象接口
"""

from .base_crawler import AbstractCrawler, AbstractStore, AbstractApiClient

__all__ = ['AbstractCrawler', 'AbstractStore', 'AbstractApiClient']

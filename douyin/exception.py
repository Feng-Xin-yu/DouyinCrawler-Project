# -*- coding: utf-8 -*-
"""
抖音爬虫异常定义
定义爬虫过程中可能出现的异常类型
"""

from httpx import RequestError


class DataFetchError(RequestError):
    """
    数据获取错误
    在获取数据时发生错误时抛出
    """
    pass


class IPBlockError(RequestError):
    """
    IP被封禁错误
    当请求过快导致服务器封禁IP时抛出
    """
    pass

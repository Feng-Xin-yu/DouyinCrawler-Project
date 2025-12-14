# -*- coding: utf-8 -*-
"""
异步HTTP客户端
封装httpx库，提供异步HTTP请求功能
用于发送HTTP请求到目标网站
"""

import logging

import httpx

# 创建日志记录器
logger = logging.getLogger(__name__)


class AsyncHTTPClient:
    """
    异步HTTP客户端类
    封装httpx.AsyncClient，提供简洁的异步HTTP请求接口
    
    设计思路：
    1. 使用httpx库实现异步HTTP请求
    2. 支持上下文管理器（async with），自动管理资源
    3. 提供GET和POST方法，简化常用请求
    """
    
    def __init__(self, base_url: str = ""):
        """
        初始化HTTP客户端
        
        Args:
            base_url: 基础URL，如果设置了，后续请求会自动拼接此URL
        """
        # 创建httpx异步客户端
        self.client = httpx.AsyncClient()
        # 保存基础URL
        self.base_uri = base_url

    async def __aenter__(self):
        """
        异步上下文管理器入口
        在进入 'async with' 块时调用
        
        Returns:
            self: 返回自身实例
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口
        在退出 'async with' 块时调用，无论是否发生异常都会关闭客户端
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        await self.close()

    async def fetch(self, method: str, url: str, **kwargs):
        """
        执行HTTP请求（通用方法）
        
        Args:
            method: HTTP方法（GET、POST、PUT、DELETE等）
            url: 请求的URL
            **kwargs: 其他请求参数（headers、params、data、json、timeout等）
            
        Returns:
            httpx.Response: HTTP响应对象
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        # 如果有基础URL，则拼接
        if self.base_uri:
            url = self.base_uri + url
            
        logger.info(f"Request started: {method} {url}, kwargs:{kwargs}")
        
        try:
            # 发送HTTP请求
            response = await self.client.request(method, url, **kwargs)
            logger.info(f"Request completed with status {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    async def get(self, url: str, **kwargs):
        """
        发送GET请求
        
        Args:
            url: 请求的URL
            **kwargs: 其他请求参数（headers、params、timeout等）
            
        Returns:
            httpx.Response: HTTP响应对象
        """
        return await self.fetch('GET', url, **kwargs)

    async def post(self, url, data=None, json=None, **kwargs):
        """
        发送POST请求
        
        Args:
            url: 请求的URL
            data: 表单数据（字典格式）
            json: JSON数据（字典格式）
            **kwargs: 其他请求参数（headers、timeout等）
            
        Returns:
            httpx.Response: HTTP响应对象
        """
        # 如果提供了json参数，则作为JSON发送
        if json is not None:
            kwargs['json'] = json
        # 如果提供了data参数，则作为表单数据发送
        elif data is not None:
            kwargs['data'] = data
        return await self.fetch('POST', url, **kwargs)

    async def close(self):
        """
        关闭HTTP客户端
        释放连接资源
        """
        await self.client.aclose()

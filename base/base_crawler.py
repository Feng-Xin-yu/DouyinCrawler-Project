# -*- coding: utf-8 -*-
"""
抽象基类定义
使用抽象基类（ABC）定义爬虫、存储、API客户端的统一接口
这是整个项目的架构基础，所有具体实现都必须遵循这些接口
"""

from abc import ABC, abstractmethod
from typing import Dict


class AbstractCrawler(ABC):
    """
    爬虫抽象基类
    所有平台的爬虫都必须继承这个类并实现其抽象方法
    
    设计思路：
    1. 使用抽象基类确保所有爬虫都有统一的接口
    2. async_initialize：异步初始化，用于初始化账号池、代理池等资源
    3. start：启动爬虫，根据不同的爬取类型执行不同的逻辑
    """
    
    @abstractmethod
    async def async_initialize(self):
        """
        异步初始化方法
        在爬虫启动前进行初始化工作，包括：
        - 初始化账号池和代理池
        - 初始化签名服务客户端
        - 加载配置信息
        - 初始化数据库连接等
        
        Returns:
            None
        """
        raise NotImplementedError("子类必须实现 async_initialize 方法")

    @abstractmethod
    async def start(self):
        """
        启动爬虫方法
        根据配置的爬取类型（搜索/详情/创作者/首页）执行相应的爬取逻辑
        
        Returns:
            None
        """
        raise NotImplementedError("子类必须实现 start 方法")


class AbstractStore(ABC):
    """
    数据存储抽象基类
    定义数据存储的统一接口，支持多种存储方式（MySQL/CSV/JSON）
    
    设计思路：
    1. 将存储逻辑抽象化，便于切换不同的存储后端
    2. 分别处理内容、评论、创作者三种数据类型
    3. 使用异步方法提高性能
    """
    
    @abstractmethod
    async def store_content(self, content_item: Dict):
        """
        存储内容数据（视频/帖子）
        
        Args:
            content_item: 内容数据字典，包含视频/帖子的所有信息
            
        Returns:
            None
        """
        raise NotImplementedError("子类必须实现 store_content 方法")

    @abstractmethod
    async def store_comment(self, comment_item: Dict):
        """
        存储评论数据
        
        Args:
            comment_item: 评论数据字典，包含评论的所有信息
            
        Returns:
            None
        """
        raise NotImplementedError("子类必须实现 store_comment 方法")

    @abstractmethod
    async def store_creator(self, creator: Dict):
        """
        存储创作者数据
        
        Args:
            creator: 创作者数据字典，包含创作者的所有信息
            
        Returns:
            None
        """
        raise NotImplementedError("子类必须实现 store_creator 方法")


class AbstractApiClient(ABC):
    """
    API客户端抽象基类
    定义HTTP请求的统一接口
    
    设计思路：
    1. 封装HTTP请求逻辑，统一处理请求头、签名、代理等
    2. 便于在不同平台间切换和扩展
    """
    
    @abstractmethod
    async def request(self, method, url, **kwargs):
        """
        发送HTTP请求
        
        Args:
            method: 请求方法（GET/POST等）
            url: 请求URL
            **kwargs: 其他请求参数（headers、params、data等）
            
        Returns:
            响应数据
        """
        raise NotImplementedError("子类必须实现 request 方法")

# -*- coding: utf-8 -*-
"""
代理IP提供商抽象基类
定义代理IP提供商的统一接口
"""

from abc import ABC, abstractmethod
from typing import List

from .types import IpInfoModel


class ProxyProvider(ABC):
    """
    代理IP提供商抽象基类
    所有代理IP提供商都必须继承此类并实现其抽象方法
    """
    
    @abstractmethod
    async def get_proxies(self, count: int) -> List[IpInfoModel]:
        """
        获取指定数量的代理IP
        
        Args:
            count: 需要获取的代理IP数量
            
        Returns:
            List[IpInfoModel]: 代理IP列表
        """
        raise NotImplementedError("子类必须实现 get_proxies 方法")

    @abstractmethod
    def mark_ip_invalid(self, ip_info: IpInfoModel):
        """
        标记IP为无效
        
        Args:
            ip_info: IP信息模型
        """
        raise NotImplementedError("子类必须实现 mark_ip_invalid 方法")

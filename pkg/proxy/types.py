# -*- coding: utf-8 -*-
"""
代理IP类型定义
定义代理IP的数据模型和提供商枚举
"""

import time
from enum import Enum

from pydantic import BaseModel, Field


class ProviderNameEnum(Enum):
    """
    代理IP提供商枚举
    """
    KUAI_DAILI_PROVIDER: str = "kuaidaili"  # 快代理


class IpInfoModel(BaseModel):
    """
    统一的IP信息模型
    存储代理IP的所有信息，包括IP、端口、认证信息、过期时间等
    """
    ip: str = Field(title="代理IP地址")
    port: int = Field(title="代理端口")
    user: str = Field(title="IP代理认证的用户名")
    protocol: str = Field(default="https://", title="代理IP的协议")
    password: str = Field(title="IP代理认证用户的密码")
    expired_time_ts: int = Field(title="IP过期时间时间戳，单位秒")

    def format_httpx_proxy(self) -> str:
        """
        格式化为httpx可用的代理URL
        
        Returns:
            str: httpx代理URL，格式：http://user:password@ip:port
        """
        return f"http://{self.user}:{self.password}@{self.ip}:{self.port}"

    @property
    def is_expired(self) -> bool:
        """
        检查IP是否已过期
        
        Returns:
            bool: True表示已过期，False表示未过期
        """
        return self.expired_time_ts < int(time.time())

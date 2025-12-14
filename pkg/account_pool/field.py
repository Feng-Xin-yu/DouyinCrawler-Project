# -*- coding: utf-8 -*-
"""
账号池数据模型
定义账号信息的数据结构
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

import constant
from pkg.proxy.types import IpInfoModel


class AccountStatusEnum(Enum):
    """
    账号状态枚举
    """
    NORMAL = 0  # 正常
    INVALID = -1  # 无效/已封禁


class AccountPlatformEnum(Enum):
    """
    账号平台枚举
    """
    DOUYIN = constant.DOUYIN_PLATFORM_NAME


class AccountInfoModel(BaseModel):
    """
    账号信息模型
    存储账号的基本信息，包括ID、名称、Cookies、状态等
    """
    id: int = Field(title="账号ID，主键，自增")
    account_name: str = Field("", title="账号名称")
    cookies: str = Field("", title="账号Cookies")
    platform_name: str = Field("", title="平台名称")
    status: int = Field(AccountStatusEnum.NORMAL.value, title="账号状态，0:正常，-1:无效")
    invalid_timestamp: int = Field(0, title="账号失效时间戳")

    def __repr__(self):
        """
        自定义表示方法，隐藏完整的Cookies信息
        """
        cookies_preview = f"{self.cookies[:5]}..." if self.cookies else "No cookies"
        return (f"AccountInfoModel(id={self.id}, "
                f"account_name='{self.account_name}', "
                f"cookies='{cookies_preview}', "
                f"platform_name={self.platform_name}, "
                f"status={self.status}, "
                f"invalid_timestamp={self.invalid_timestamp})")

    def __str__(self):
        """
        字符串表示方法
        """
        return self.__repr__()


class AccountWithIpModel(BaseModel):
    """
    账号与IP配对模型
    将账号和代理IP绑定在一起，确保请求的一致性
    """
    account: AccountInfoModel
    ip_info: Optional[IpInfoModel] = None

    def __repr__(self):
        """
        自定义表示方法
        """
        return f"AccountWithIpModel(account={repr(self.account)}, ip_info={self.ip_info})"

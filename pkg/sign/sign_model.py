# -*- coding: utf-8 -*-
"""
签名数据模型
定义签名请求和响应的数据结构
"""

from typing import Optional

from pydantic import BaseModel, Field


class DouyinSignResult(BaseModel):
    """
    抖音签名结果
    包含生成的签名参数
    """
    a_bogus: str = Field(..., title="a_bogus", description="抖音请求签名参数a_bogus")


class DouyinSignRequest(BaseModel):
    """
    抖音签名请求
    包含生成签名所需的所有参数
    """
    uri: str = Field(..., title="request_uri", description="请求的URI")
    query_params: str = Field(..., title="query_params", description="请求的query_params（URL编码后的参数）")
    user_agent: str = Field(..., title="user_agent", description="请求的User-Agent")
    cookies: str = Field(..., title="cookies", description="请求的Cookies")


class DouyinSignResponse(BaseModel):
    """
    抖音签名响应
    包含签名结果和状态信息
    
    支持两种格式：
    1. 直接包含a_bogus字段
    2. 包含data字段
    """
    biz_code: int = 0
    msg: str = "OK!"
    isok: bool = True
    data: Optional[DouyinSignResult] = None
    # 直接包含a_bogus字段
    a_bogus: Optional[str] = None
    
    def get_a_bogus(self) -> str:
        """
        获取a_bogus参数
        兼容两种格式：直接字段或data字段
        """
        if self.a_bogus:
            return self.a_bogus
        elif self.data and self.data.a_bogus:
            return self.data.a_bogus
        else:
            raise ValueError("a_bogus not found in response")

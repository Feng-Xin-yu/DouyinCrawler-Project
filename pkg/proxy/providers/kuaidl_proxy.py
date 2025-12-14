# -*- coding: utf-8 -*-
"""
快代理HTTP实现
快代理官方文档：https://www.kuaidaili.com/
"""

import re
from typing import List

import httpx
from pydantic import BaseModel, Field

import config
from pkg.proxy.base_proxy import ProxyProvider
from pkg.proxy.types import IpInfoModel, ProviderNameEnum
from pkg.tools import utils

# 快代理的IP代理过期时间向前推移5秒（提前过期，避免使用过期IP）
DELTA_EXPIRED_SECOND = 5


class KuaidailiProxyModel(BaseModel):
    """
    快代理IP信息模型
    """
    ip: str = Field(title="IP地址")
    port: int = Field(title="端口")
    expire_ts: int = Field(title="过期时间，单位秒，多少秒后过期")


def parse_kuaidaili_proxy(proxy_info: str) -> KuaidailiProxyModel:
    """
    解析快代理的IP信息
    格式：ip:port,expire_ts
    
    Args:
        proxy_info: 快代理返回的IP信息字符串
        
    Returns:
        KuaidailiProxyModel: 解析后的IP信息模型
        
    Raises:
        Exception: 如果解析失败
    """
    # 使用正则表达式解析IP信息
    pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5}),(\d+)'
    match = re.search(pattern, proxy_info)
    if not match or not match.groups():
        raise Exception("not match kuaidaili proxy info")

    return KuaidailiProxyModel(
        ip=match.groups()[0],
        port=int(match.groups()[1]),
        expire_ts=int(match.groups()[2])
    )


class KuaiDaiLiProxy(ProxyProvider):
    """
    快代理提供商实现
    从快代理API获取代理IP
    """
    
    def __init__(
        self,
        kdl_user_name: str,
        kdl_user_pwd: str,
        kdl_secret_id: str,
        kdl_signature: str
    ):
        """
        初始化快代理提供商
        
        Args:
            kdl_user_name: 快代理用户名
            kdl_user_pwd: 快代理密码
            kdl_secret_id: 快代理Secret ID
            kdl_signature: 快代理签名
        """
        self.kdl_user_name = kdl_user_name
        self.kdl_user_pwd = kdl_user_pwd
        self.api_base = "https://dps.kdlapi.com/"
        self.secret_id = kdl_secret_id
        self.signature = kdl_signature
        self.proxy_brand_name = ProviderNameEnum.KUAI_DAILI_PROVIDER.value
        
        # API请求参数
        self.params = {
            "secret_id": self.secret_id,
            "signature": self.signature,
            "pt": 1,  # 代理类型：1-私密代理
            "format": "json",  # 返回格式
            "sep": 1,  # 分隔符
            "f_et": 1,  # 返回过期时间
        }

    async def get_proxies(self, num: int) -> List[IpInfoModel]:
        """
        从快代理获取指定数量的代理IP
        
        Args:
            num: 需要获取的IP数量
            
        Returns:
            List[IpInfoModel]: 代理IP列表
            
        Raises:
            Exception: 如果获取失败
        """
        uri = "/api/getdps/"
        self.params.update({"num": num})

        ip_infos: List[IpInfoModel] = []
        async with httpx.AsyncClient() as client:
            response = await client.get(self.api_base + uri, params=self.params)

            if response.status_code != 200:
                utils.logger.error(
                    f"[KuaiDaiLiProxy.get_proxies] status code not 200 and response.txt:{response.text}"
                )
                raise Exception("get ip error from proxy provider and status code not 200 ...")

            ip_response = response.json()
            if ip_response.get("code") != 0:
                utils.logger.error(
                    f"[KuaiDaiLiProxy.get_proxies] code not 0 and msg:{ip_response.get('msg')}"
                )
                raise Exception("get ip error from proxy provider and code not 0 ...")

            proxy_list: List[str] = ip_response.get("data", {}).get("proxy_list", [])
            for proxy in proxy_list:
                proxy_model = parse_kuaidaili_proxy(proxy)
                ip_info_model = IpInfoModel(
                    ip=proxy_model.ip,
                    port=proxy_model.port,
                    user=self.kdl_user_name,
                    password=self.kdl_user_pwd,
                    # 计算过期时间戳（当前时间 + 过期秒数 - 提前量）
                    expired_time_ts=proxy_model.expire_ts + utils.get_unix_timestamp() - DELTA_EXPIRED_SECOND,
                )
                ip_infos.append(ip_info_model)

        return ip_infos

    def mark_ip_invalid(self, ip_info: IpInfoModel) -> None:
        """
        标记IP为无效
        快代理不需要特殊处理，只需要记录日志
        
        Args:
            ip_info: IP信息模型
        """
        utils.logger.info(
            f"[KuaiDaiLiProxy.mark_ip_invalid] mark {ip_info.ip}:{ip_info.port} invalid"
        )


def new_kuai_daili_proxy() -> KuaiDaiLiProxy:
    """
    构造快代理HTTP实例
    从配置中读取快代理的认证信息
    
    Returns:
        KuaiDaiLiProxy: 快代理提供商实例
    """
    return KuaiDaiLiProxy(
        kdl_secret_id=config.KDL_SECERT_ID,
        kdl_signature=config.KDL_SIGNATURE,
        kdl_user_name=config.KDL_USER_NAME,
        kdl_user_pwd=config.KDL_USER_PWD,
    )

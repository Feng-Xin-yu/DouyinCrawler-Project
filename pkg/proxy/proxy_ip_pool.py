# -*- coding: utf-8 -*-
"""
代理IP池实现
管理代理IP的获取、验证、轮换等功能
"""

import random
from typing import Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

import config
from pkg.proxy.providers import new_kuai_daili_proxy
from pkg.tools import utils

from .base_proxy import ProxyProvider
from .types import IpInfoModel, ProviderNameEnum


class ProxyIpPool:
    """
    代理IP池
    负责管理代理IP的获取、验证、轮换等功能
    
    设计思路：
    1. 从代理IP提供商获取IP
    2. 可选地验证IP是否有效
    3. 支持IP轮换和失效标记
    """
    
    def __init__(
        self, ip_pool_count: int, enable_validate_ip: bool, ip_provider: ProxyProvider
    ) -> None:
        """
        初始化代理IP池
        
        Args:
            ip_pool_count: IP池的数量
            enable_validate_ip: 是否启用IP验证
            ip_provider: 代理IP提供商
        """
        # 验证IP是否有效的测试URL
        self.valid_ip_url = "https://echo.apifox.cn/"
        self.ip_pool_count = ip_pool_count
        self.enable_validate_ip = enable_validate_ip
        self.proxy_list: List[IpInfoModel] = []
        self.ip_provider: ProxyProvider = ip_provider

    async def load_proxies(self) -> None:
        """
        加载IP代理
        从代理IP提供商获取指定数量的IP
        """
        self.proxy_list = await self.ip_provider.get_proxies(self.ip_pool_count)

    async def _is_valid_proxy(self, proxy: IpInfoModel) -> bool:
        """
        验证代理IP是否有效
        通过访问测试URL来验证IP是否可用
        
        Args:
            proxy: 代理IP信息模型
            
        Returns:
            bool: True表示有效，False表示无效
        """
        utils.logger.info(
            f"[ProxyIpPool._is_valid_proxy] testing {proxy.ip} is it valid "
        )
        try:
            # 格式化代理URL
            httpx_proxy = f"http://{proxy.user}:{proxy.password}@{proxy.ip}:{proxy.port}"
            # httpx 0.28.0 可以直接使用 proxy 参数
            async with httpx.AsyncClient(proxy=httpx_proxy, timeout=10) as client:
                response = await client.get(self.valid_ip_url)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            utils.logger.info(
                f"[ProxyIpPool._is_valid_proxy] testing {proxy.ip} err: {e}"
            )
            return False

    async def mark_ip_invalid(self, proxy: IpInfoModel):
        """
        标记IP为无效
        从代理池中移除该IP，并通知提供商
        
        Args:
            proxy: 代理IP信息模型
        """
        utils.logger.info(f"[ProxyIpPool.mark_ip_invalid] mark {proxy.ip} invalid")
        # 通知提供商标记IP为无效
        self.ip_provider.mark_ip_invalid(proxy)
        # 从代理池中移除该IP
        for p in self.proxy_list:
            if (
                p.ip == proxy.ip
                and p.port == proxy.port
                and p.protocol == proxy.protocol
                and p.user == proxy.user
                and p.password == proxy.password
            ):
                self.proxy_list.remove(p)
                break

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def get_proxy(self) -> IpInfoModel:
        """
        从代理池中随机提取一个代理IP
        如果代理池为空，则重新加载
        如果启用了验证，则验证IP是否有效
        
        Returns:
            IpInfoModel: 代理IP信息模型
            
        Raises:
            Exception: 如果IP无效且重试失败
        """
        # 如果代理池为空，重新加载
        if len(self.proxy_list) == 0:
            await self._reload_proxies()

        # 随机选择一个IP
        proxy = random.choice(self.proxy_list)
        # 从列表中移除（避免重复使用）
        self.proxy_list.remove(proxy)
        
        # 如果启用了验证，验证IP是否有效
        if self.enable_validate_ip:
            if not await self._is_valid_proxy(proxy):
                raise Exception(
                    "[ProxyIpPool.get_proxy] current ip invalid and again get it"
                )
        return proxy

    async def _reload_proxies(self):
        """
        重新加载代理池
        清空当前代理列表，重新从提供商获取
        """
        self.proxy_list = []
        await self.load_proxies()


# 代理IP提供商字典
IpProxyProvider: Dict[str, ProxyProvider] = {
    ProviderNameEnum.KUAI_DAILI_PROVIDER.value: new_kuai_daili_proxy()
}


async def create_ip_pool(
    ip_pool_count: int,
    enable_validate_ip: bool,
    ip_provider=config.IP_PROXY_PROVIDER_NAME,
) -> ProxyIpPool:
    """
    创建IP代理池的工厂函数
    
    Args:
        ip_pool_count: IP池的数量
        enable_validate_ip: 是否启用IP验证
        ip_provider: 代理IP提供商名称，默认使用配置中的值
        
    Returns:
        ProxyIpPool: 代理IP池实例
    """
    pool = ProxyIpPool(
        ip_pool_count=ip_pool_count,
        enable_validate_ip=enable_validate_ip,
        ip_provider=IpProxyProvider.get(ip_provider),
    )
    await pool.load_proxies()
    return pool

# -*- coding: utf-8 -*-
"""
账号池管理器
管理多个账号，支持账号轮换、状态管理和与代理IP的配对
"""

import asyncio
import os
from typing import Dict, List, Optional

import pandas as pd

import config
import constant
from constant import EXCEL_ACCOUNT_SAVE
from pkg.account_pool.field import (
    AccountInfoModel,
    AccountStatusEnum,
    AccountWithIpModel
)
from pkg.proxy.types import IpInfoModel
from pkg.proxy.proxy_ip_pool import ProxyIpPool
from pkg.tools import utils


class AccountPoolManager:
    """
    账号池管理器
    负责管理多个账号，支持从Excel加载账号，支持账号状态管理
    """
    
    def __init__(self, platform_name: str, account_save_type: str):
        """
        初始化账号池管理器
        
        Args:
            platform_name: 平台名称，例如：'dy'（抖音）
            account_save_type: 账号存储类型，仅支持'xlsx'
        """
        self._platform_name = platform_name
        self._account_save_type = account_save_type
        self._account_list: List[AccountInfoModel] = []

    async def async_initialize(self):
        """
        异步初始化
        从Excel文件加载账号
        """
        if self._account_save_type == EXCEL_ACCOUNT_SAVE:
            self.load_accounts_from_xlsx()
        else:
            raise ValueError(f"不支持的账号存储类型: {self._account_save_type}，仅支持 {EXCEL_ACCOUNT_SAVE}")

    def load_accounts_from_xlsx(self):
        """
        从Excel文件加载账号
        Excel文件路径：config/accounts_cookies.xlsx
        """
        utils.logger.info(
            f"[AccountPoolManager.load_accounts_from_xlsx] load account from {self._platform_name} accounts_cookies.xlsx"
        )
        # Excel文件路径
        account_cookies_file_name = "../../config/accounts_cookies.xlsx"
        account_cookies_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), account_cookies_file_name
        )
        
        # 读取Excel文件
        df = pd.read_excel(
            account_cookies_file_path, sheet_name=self._platform_name, engine="openpyxl"
        )
        
        account_id = 1
        for _, row in df.iterrows():
            account = AccountInfoModel(
                id=row.get("id", account_id),
                account_name=row.get("account_name", ""),
                cookies=row.get("cookies", ""),
                status=AccountStatusEnum.NORMAL.value,
                platform_name=self._platform_name,
            )
            self.add_account(account)
            account_id += 1
            utils.logger.info(
                f"[AccountPoolManager.load_accounts_from_xlsx] load account {account}"
            )
        utils.logger.info(
            f"[AccountPoolManager.load_accounts_from_xlsx] all account load success"
        )


    def get_active_account(self) -> AccountInfoModel:
        """
        获取一个可用的账号（状态为NORMAL）
        
        Returns:
            AccountInfoModel: 账号信息模型
            
        Raises:
            Exception: 如果没有可用的账号
        """
        # 首先尝试从现有列表中查找NORMAL状态的账号（不移除）
        for account in self._account_list:
            if account.status == AccountStatusEnum.NORMAL.value:
                utils.logger.info(
                    f"[AccountPoolManager.get_active_account] get active account {account}"
                )
                return account

        # 如果没有找到可用账号，尝试重新加载账号池
        utils.logger.warning(
            "[AccountPoolManager.get_active_account] No active account found, try to reload account pool"
        )
        self._reload_accounts()
        
        # 重新加载后再次查找
        for account in self._account_list:
            if account.status == AccountStatusEnum.NORMAL.value:
                utils.logger.info(
                    f"[AccountPoolManager.get_active_account] get active account after reload: {account}"
                )
                return account

        error = Exception("账号池中没有可用的账号")
        utils.log_error_with_context(
            utils.logger,
            error,
            context={
                "账号池类型": self._account_save_type,
                "平台名称": self._platform_name,
                "账号总数": len(self._account_list),
                "建议": "检查config/accounts_cookies.xlsx，确保至少有一个状态为NORMAL的账号",
            },
            level="CRITICAL"
        )
        raise error
    
    def _reload_accounts(self):
        """
        重新加载账号池
        当账号池中没有可用账号时，尝试重新加载
        """
        utils.logger.info(
            f"[AccountPoolManager._reload_accounts] Reloading account pool for {self._platform_name}"
        )
        # 清空当前列表
        self._account_list.clear()
        
        # 重新加载账号（仅支持Excel）
        if self._account_save_type == EXCEL_ACCOUNT_SAVE:
            self.load_accounts_from_xlsx()
        else:
            utils.logger.error(
                f"[AccountPoolManager._reload_accounts] Unsupported account save type: {self._account_save_type}"
            )

    def add_account(self, account: AccountInfoModel):
        """
        添加账号到账号池
        
        Args:
            account: 账号信息模型
        """
        self._account_list.append(account)

    async def update_account_status(
        self, account: AccountInfoModel, status: AccountStatusEnum
    ):
        """
        更新账号状态
        
        Args:
            account: 账号信息模型
            status: 账号状态枚举
        """
        account.status = status.value
        account.invalid_timestamp = utils.get_current_timestamp()
        
        # Excel中的账户状态暂时不更新（仅内存中更新）
        utils.logger.info(
            f"[AccountPoolManager.update_account_status] Account {account.account_name} status updated to {status.value} (in memory only)"
        )


class AccountWithIpPoolManager(AccountPoolManager):
    """
    账号与IP配对管理器
    继承自AccountPoolManager，增加了代理IP配对功能
    确保每个账号都绑定一个代理IP，提高请求的一致性
    """
    
    def __init__(
        self,
        platform_name: str,
        account_save_type: str,
        proxy_ip_pool: Optional[ProxyIpPool] = None,
    ):
        """
        初始化账号与IP配对管理器
        
        Args:
            platform_name: 平台名称
            account_save_type: 账号存储类型
            proxy_ip_pool: 代理IP池，如果为None则不使用代理IP
        """
        super().__init__(platform_name, account_save_type)
        self.proxy_ip_pool = proxy_ip_pool

    async def async_initialize(self):
        """
        异步初始化
        """
        await super().async_initialize()

    async def get_account_with_ip_info(self) -> AccountWithIpModel:
        """
        获取账号与IP配对信息
        如果proxy_ip_pool为None，则只返回账号信息
        
        Returns:
            AccountWithIpModel: 账号与IP配对模型
            
        Raises:
            Exception: 如果没有可用的账号
        """
        ip_info: Optional[IpInfoModel] = None
        
        try:
            account: AccountInfoModel = self.get_active_account()
        except Exception:
            # 如果获取账号失败，尝试重新加载账号池
            utils.logger.info(
                "[AccountWithIpPoolManager.get_account_with_ip_info] No active account, reloading from Excel"
            )
            self._reload_accounts()
            account: AccountInfoModel = self.get_active_account()
        
        # 如果启用了代理IP池，则获取一个代理IP
        if self.proxy_ip_pool:
            ip_info = await self.proxy_ip_pool.get_proxy()
            utils.logger.info(
                f"[AccountWithIpPoolManager.get_account_with_ip] enable proxy ip pool, get proxy ip: {ip_info}"
            )
        
        return AccountWithIpModel(account=account, ip_info=ip_info)

    async def mark_account_invalid(self, account: AccountInfoModel):
        """
        标记账号为无效
        
        Args:
            account: 账号信息模型
        """
        await self.update_account_status(account, AccountStatusEnum.INVALID)

    async def mark_ip_invalid(self, ip_info: Optional[IpInfoModel]):
        """
        标记IP为无效
        
        Args:
            ip_info: IP信息模型
        """
        if not ip_info:
            return
        if self.proxy_ip_pool:
            await self.proxy_ip_pool.mark_ip_invalid(ip_info)

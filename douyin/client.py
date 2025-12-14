# -*- coding: utf-8 -*-
"""
抖音API客户端
负责与抖音API通信，包括发送请求、处理签名、管理账号等
这是爬虫的核心组件之一
"""

import asyncio
import copy
import json
import traceback
import urllib.parse
from typing import Dict, List, Optional, Tuple, Union

import httpx
from httpx import Response
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

import config
from base.base_crawler import AbstractApiClient
from constant.douyin import DOUYIN_API_URL, DOUYIN_FIXED_USER_AGENT
from model.m_douyin import DouyinAweme, DouyinAwemeComment, DouyinCreator
from pkg.account_pool import AccountWithIpModel
from pkg.account_pool.pool import AccountWithIpPoolManager
from pkg.sign import DouyinSignLogic
from pkg.sign.sign_model import DouyinSignRequest
from pkg.tools import utils
from var import request_keyword_var

from .exception import DataFetchError
from .extractor import DouyinExtractor
from .field import (
    HomeFeedTagIdType,
    PublishTimeType,
    SearchChannelType,
    SearchSortType
)
from .help import CommonVerifyParams


class DouYinApiClient(AbstractApiClient):
    """
    抖音API客户端
    实现AbstractApiClient接口，提供抖音API的完整访问功能
    
    主要功能：
    1. 发送HTTP请求到抖音API
    2. 处理请求签名（a_bogus参数）
    3. 管理账号和代理IP
    4. 提供各种API调用方法（搜索、详情、评论、创作者、首页）
    """
    
    def __init__(
        self,
        timeout: int = 10,
        user_agent: str = None,
        common_verify_params: CommonVerifyParams = None,
        account_with_ip_pool: AccountWithIpPoolManager = None,
    ):
        """
        初始化抖音API客户端
        
        Args:
            timeout: 请求超时时间（秒），默认10秒
            user_agent: 自定义的User-Agent，默认使用固定UA
            common_verify_params: 通用验证参数（ms_token、webid等）
            account_with_ip_pool: 账号池管理器
        """
        self.timeout = timeout
        self._user_agent = user_agent or DOUYIN_FIXED_USER_AGENT
        # 使用本地签名逻辑，不再通过HTTP RPC调用
        import config
        sign_type = getattr(config, 'SIGN_TYPE', 'javascript')
        self._sign_logic = DouyinSignLogic(sign_type=sign_type)
        self.common_verify_params = common_verify_params
        self.account_with_ip_pool = account_with_ip_pool
        self.account_info: Optional[AccountWithIpModel] = None
        self._extractor = DouyinExtractor()
        # HTTP客户端缓存，避免频繁创建
        self._http_client: Optional[httpx.AsyncClient] = None
        self._cached_proxy: Optional[str] = None

    @property
    def _headers(self):
        """
        获取请求头
        包含Cookie、User-Agent、Referer等必要信息
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "accept-language": "zh-CN,zh;q=0.9",
            "Cookie": self._cookies,
            "origin": "https://www.douyin.com",
            "referer": "https://www.douyin.com/user/self",
            "user-agent": self._user_agent,
        }

    @property
    def _proxies(self):
        """
        获取代理配置
        如果账号绑定了代理IP，返回代理URL，否则返回None
        """
        return (
            self.account_info.ip_info.format_httpx_proxy()
            if self.account_info and self.account_info.ip_info
            else None
        )

    @property
    def _cookies(self):
        """
        获取Cookies
        从当前账号信息中获取Cookies
        """
        if not self.account_info:
            return ""
        return self.account_info.account.cookies

    @property
    def _common_params(self):
        """
        获取通用请求参数
        这些参数是抖音API要求的固定参数，模拟浏览器环境
        """
        return {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "publish_video_strategy_type": 2,
            "update_version_code": 170400,
            "pc_client_type": 1,
            "version_code": 170400,
            "version_name": "17.4.0",
            "cookie_enabled": "true",
            "screen_width": 2560,
            "screen_height": 1440,
            "browser_language": "zh-CN",
            "browser_platform": "MacIntel",
            "browser_name": "Chrome",
            "browser_version": "135.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "135.0.0.0",
            "os_name": "Mac+OS",
            "os_version": "10.15.7",
            "cpu_core_num": 8,
            "device_memory": 8,
            "platform": "PC",
            "downlink": 4.45,
            "effective_type": "4g",
            "round_trip_time": 100,
        }

    @property
    def _verify_params(self):
        """
        获取验证参数
        包含webid和msToken，这些是抖音请求必需的验证参数
        """
        if not self.common_verify_params:
            return {}
        return {
            "webid": self.common_verify_params.webid,
            "msToken": self.common_verify_params.ms_token,
        }

    async def update_account_info(self):
        """
        更新客户端的账号信息
        从账号池中获取一个新的账号，并验证账号是否可用
        如果账号不可用，会继续尝试获取下一个账号
        
        为了避免无限循环，设置最大重试次数
        """
        have_account = False
        max_retries = 10  # 最大重试次数，避免无限循环
        retry_count = 0
        
        while not have_account and retry_count < max_retries:
            retry_count += 1
            utils.logger.info(
                f"[DouYinApiClient.update_account_info] try to get a new account (attempt {retry_count}/{max_retries})"
            )
            
            try:
                account_info = await self.account_with_ip_pool.get_account_with_ip_info()
                # 如果账号或IP变化了，清除HTTP客户端缓存
                if self.account_info is None or (
                    self.account_info.account.id != account_info.account.id or
                    (self.account_info.ip_info and account_info.ip_info and
                     self.account_info.ip_info.ip != account_info.ip_info.ip)
                ):
                    # 清除HTTP客户端缓存，下次请求时会创建新的客户端
                    await self._reset_http_client()
                
                self.account_info = account_info
                have_account = await self.pong()
                if not have_account:
                    utils.logger.info(
                        f"[DouYinApiClient.update_account_info] current account "
                        f"{account_info.account.account_name} is invalid, try to get a new one"
                    )
                    # 标记账号为无效
                    await self.mark_account_invalid(account_info)
            except Exception as e:
                utils.logger.error(
                    f"[DouYinApiClient.update_account_info] Failed to get account: {e}"
                )
                # 如果获取账号失败，等待一段时间后重试
                if retry_count < max_retries:
                    await asyncio.sleep(2)
        
        if not have_account:
            error = Exception("Failed to get valid account after maximum retries")
            utils.log_error_with_context(
                utils.logger,
                error,
                context={
                    "重试次数": max_retries,
                    "账号池类型": self.account_with_ip_pool._account_save_type,
                    "平台名称": self.account_with_ip_pool._platform_name,
                    "建议": "检查config/accounts_cookies.xlsx中的账号配置，确保至少有一个有效账号",
                },
                level="CRITICAL"
            )
            raise error

    async def mark_account_invalid(self, account_with_ip: AccountWithIpModel):
        """
        标记账号为无效
        当账号被封禁或失效时调用此方法
        
        Args:
            account_with_ip: 账号与IP配对模型
        """
        if self.account_with_ip_pool:
            await self.account_with_ip_pool.mark_account_invalid(
                account_with_ip.account
            )
            await self.account_with_ip_pool.mark_ip_invalid(account_with_ip.ip_info)

    async def _pre_url_params(self, uri: str, url_params: Dict) -> Dict:
        """
        预处理URL参数，生成a_bogus签名参数
        这是抖音反爬虫的关键，每个请求都需要生成a_bogus参数
        
        Args:
            uri: 请求URI
            url_params: 原始URL参数
            
        Returns:
            Dict: 包含a_bogus的完整参数字典
        """
        # 复制参数，避免修改原始参数
        final_url_params = copy.copy(url_params or {})
        # 合并通用参数和验证参数
        final_url_params.update(self._common_params)
        final_url_params.update(self._verify_params)
        
        # 将参数编码为URL查询字符串
        query_params = urllib.parse.urlencode(final_url_params)
        
        # 调用签名逻辑生成a_bogus参数
        sign_req: DouyinSignRequest = DouyinSignRequest(
            uri=uri,
            query_params=query_params,
            user_agent=self._user_agent,
            cookies=self._cookies,
        )
        dy_sign_resp = await self._sign_logic.sign(sign_req)
        
        # 某些接口不需要a_bogus参数（如搜索接口）
        if "/v1/web/general/search/single/" not in uri:
            # 获取a_bogus参数（兼容两种格式：直接字段或data字段）
            if hasattr(dy_sign_resp, 'get_a_bogus'):
                a_bogus = dy_sign_resp.get_a_bogus()
            elif hasattr(dy_sign_resp, 'a_bogus') and dy_sign_resp.a_bogus:
                a_bogus = dy_sign_resp.a_bogus
            elif hasattr(dy_sign_resp, 'data') and dy_sign_resp.data and hasattr(dy_sign_resp.data, 'a_bogus'):
                a_bogus = dy_sign_resp.data.a_bogus
            else:
                utils.logger.error("[DouYinApiClient._pre_url_params] Failed to get a_bogus from sign response")
                raise Exception("Failed to generate a_bogus signature")
            
            if a_bogus:
                final_url_params["a_bogus"] = a_bogus
            else:
                utils.logger.error("[DouYinApiClient._pre_url_params] a_bogus is empty")
                raise Exception("Failed to generate a_bogus signature")

        return final_url_params

    async def check_ip_expired(self):
        """
        检查IP是否过期
        由于IP的过期时间在运行中是不确定的，所以每次请求都需要验证IP是否过期
        如果过期了，需要重新获取一个新的IP
        """
        if (
            config.ENABLE_IP_PROXY
            and self.account_info
            and self.account_info.ip_info
            and self.account_info.ip_info.is_expired
        ):
            utils.logger.info(
                f"[DouYinApiClient.check_ip_expired] current ip {self.account_info.ip_info.ip} is expired, "
                f"mark it invalid and try to get a new one"
            )
            await self.account_with_ip_pool.mark_ip_invalid(self.account_info.ip_info)
            self.account_info.ip_info = (
                await self.account_with_ip_pool.proxy_ip_pool.get_proxy()
            )
            # IP变化了，清除HTTP客户端缓存
            await self._reset_http_client()

    async def _reset_http_client(self):
        """
        重置HTTP客户端
        当账号或IP变化时调用，清除缓存的HTTP客户端
        """
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
            self._cached_proxy = None
            utils.logger.debug(
                "[DouYinApiClient._reset_http_client] HTTP client cache cleared"
            )

    async def cleanup(self):
        """
        清理资源
        关闭HTTP客户端连接
        """
        await self._reset_http_client()

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(1))
    async def request(self, method, url, **kwargs) -> Union[Response, Dict]:
        """
        封装httpx的公共请求方法
        对请求响应进行处理，包括错误处理和重试机制
        
        Args:
            method: HTTP方法（GET、POST等）
            url: 请求的URL
            **kwargs: 其他请求参数（headers、params、data等）
            
        Returns:
            Union[Response, Dict]: 响应对象或JSON字典
            
        Raises:
            DataFetchError: 如果请求失败
        """
        # 检查IP是否过期
        await self.check_ip_expired()
        
        # 处理是否需要返回原始响应
        need_return_ori_response = kwargs.get("return_response", False)
        if "return_response" in kwargs:
            del kwargs["return_response"]

        # 如果没有提供headers，使用默认headers
        if "headers" not in kwargs:
            kwargs["headers"] = self._headers

        # 获取当前代理配置
        current_proxy = self._proxies
        
        # 如果代理配置变化了，需要重新创建HTTP客户端
        if self._http_client is None or self._cached_proxy != current_proxy:
            # 关闭旧的客户端（如果存在）
            if self._http_client is not None:
                await self._http_client.aclose()
            # 创建新的客户端
            self._http_client = httpx.AsyncClient(proxy=current_proxy, timeout=self.timeout)
            self._cached_proxy = current_proxy
            utils.logger.debug(
                f"[DouYinApiClient.request] Created new HTTP client with proxy: {current_proxy}"
            )
        
        # 使用缓存的HTTP客户端发送请求
        response = await self._http_client.request(method, url, **kwargs)

        # 如果需要返回原始响应，直接返回
        if need_return_ori_response:
            return response

        # 检查HTTP状态码
        if response.status_code == 401:
            # 401 Unauthorized - 账号未授权，可能cookie失效
            error = Exception("account unauthorized")
            utils.log_error_with_context(
                utils.logger,
                error,
                context={
                    "HTTP状态码": 401,
                    "请求URL": url,
                    "请求方法": method,
                    "当前账号": self.account_info.account.account_name if self.account_info else "未知",
                    "响应内容": response.text[:500] if response.text else "空响应",
                }
            )
            raise error
        elif response.status_code == 403:
            # 403 Forbidden - 账号被封禁或IP被限制
            error = Exception("account blocked")
            utils.log_error_with_context(
                utils.logger,
                error,
                context={
                    "HTTP状态码": 403,
                    "请求URL": url,
                    "请求方法": method,
                    "当前账号": self.account_info.account.account_name if self.account_info else "未知",
                    "当前IP": self.account_info.ip_info.ip if (self.account_info and self.account_info.ip_info) else "未使用代理",
                    "响应内容": response.text[:500] if response.text else "空响应",
                }
            )
            raise error
        elif response.status_code == 429:
            # 429 Too Many Requests - 请求过于频繁，需要等待
            error = Exception("rate limited")
            utils.log_error_with_context(
                utils.logger,
                error,
                context={
                    "HTTP状态码": 429,
                    "请求URL": url,
                    "请求方法": method,
                    "建议": "等待10秒后重试，或增加请求间隔时间",
                },
                level="WARNING"
            )
            raise error
        elif response.status_code != 200:
            # 其他非200状态码
            error = DataFetchError(f"HTTP {response.status_code} error")
            utils.log_error_with_context(
                utils.logger,
                error,
                context={
                    "HTTP状态码": response.status_code,
                    "请求URL": url,
                    "请求方法": method,
                    "响应内容": response.text[:500] if response.text else "空响应",
                    "响应头": dict(response.headers) if hasattr(response, 'headers') else "未知",
                }
            )
            raise error

        # 处理响应
        try:
            # 检查是否被拦截（通过响应内容判断）
            if response.text == "" or response.text == "blocked":
                utils.logger.error(
                    f"[DouYinApiClient.request] Request blocked, response.text: {response.text}"
                )
                raise Exception("account blocked")
            
            # 尝试解析JSON
            try:
                json_data = response.json()
            except Exception as json_error:
                error = DataFetchError(f"Failed to parse JSON response: {json_error}")
                utils.log_error_with_context(
                    utils.logger,
                    error,
                    context={
                        "请求URL": url,
                        "响应状态码": response.status_code,
                        "响应内容前500字符": response.text[:500] if response.text else "空响应",
                    }
                )
                raise error
            
            # 检查API返回的状态码（抖音API会在JSON中返回status_code字段）
            api_status_code = json_data.get("status_code", 0)
            if api_status_code == 8:
                # status_code == 8 表示未登录
                error = Exception("account not logged in")
                utils.log_error_with_context(
                    utils.logger,
                    error,
                    context={
                        "API状态码": 8,
                        "请求URL": url,
                        "当前账号": self.account_info.account.account_name if self.account_info else "未知",
                        "API响应": json_data,
                    }
                )
                raise error
            elif api_status_code != 0 and api_status_code != 1:
                # status_code != 0 且 != 1 表示API错误
                status_msg = json_data.get("status_msg", "Unknown error")
                # 对于某些错误码，仍然返回数据（让上层处理）
                # 但对于明显的账号错误，抛出异常
                if api_status_code in [8, 10007, 10008]:  # 常见的账号相关错误码
                    error = Exception(f"account error: {status_msg}")
                    utils.log_error_with_context(
                        utils.logger,
                        error,
                        context={
                            "API状态码": api_status_code,
                            "API错误消息": status_msg,
                            "请求URL": url,
                            "当前账号": self.account_info.account.account_name if self.account_info else "未知",
                        },
                        level="WARNING"
                    )
                    raise error
                else:
                    # 其他错误码，记录警告但不抛出异常
                    utils.logger.warning(
                        f"[DouYinApiClient.request] API status_code={api_status_code}, status_msg={status_msg}. URL: {url}"
                    )
            
            return json_data
        except Exception as e:
            # 如果已经是我们定义的异常，直接抛出（已经在上面记录过详细信息）
            if isinstance(e, (Exception,)) and str(e) in [
                "account blocked", "account unauthorized", "account not logged in", 
                "rate limited", "account error"
            ]:
                raise
            # 其他异常（如JSON解析错误），记录详细信息后抛出
            error = DataFetchError(f"{e}")
            utils.log_error_with_context(
                utils.logger,
                error,
                context={
                    "请求URL": url,
                    "请求方法": method,
                    "响应状态码": response.status_code if hasattr(response, 'status_code') else "未知",
                    "响应内容": response.text[:500] if (hasattr(response, 'text') and response.text) else "空响应",
                }
            )
            raise error

    async def get(self, uri: str, params: Optional[Dict] = None, **kwargs):
        """
        GET请求方法
        自动处理签名和重试逻辑
        
        Args:
            uri: 请求URI
            params: 请求参数
            **kwargs: 其他请求参数
            
        Returns:
            Dict: API响应JSON数据
        """
        try:
            # 预处理参数，生成签名
            params = await self._pre_url_params(uri, params)
            return await self.request(
                method="GET", url=f"{DOUYIN_API_URL}{uri}", params=params, **kwargs
            )
        except RetryError as e:
            # 获取原始异常
            original_exception = e.last_attempt.exception()
            exception_str = str(original_exception)
            traceback.print_exception(
                type(original_exception),
                original_exception,
                original_exception.__traceback__,
            )
            
            # 根据异常类型采取不同的处理策略
            account_related_errors = [
                "account blocked", "account unauthorized", "account not logged in", 
                "account error"
            ]
            
            if any(err in exception_str for err in account_related_errors):
                # 账号相关错误：立即标记账号无效并换账号
                utils.logger.error(
                    f"[DouYinApiClient.get] 账号相关错误: {exception_str}, 尝试更换账号与IP"
                )
                await self.mark_account_invalid(self.account_info)
                await self.update_account_info()
                params = await self._pre_url_params(uri, params)
                return await self.request(
                    method="GET", url=f"{DOUYIN_API_URL}{uri}", params=params, **kwargs
                )
            elif "rate limited" in exception_str:
                # 频率限制：等待更长时间后重试
                utils.logger.warning(
                    f"[DouYinApiClient.get] 请求频率受限，等待10秒后重试: {uri}"
                )
                await asyncio.sleep(10)
                params = await self._pre_url_params(uri, params)
                return await self.request(
                    method="GET", url=f"{DOUYIN_API_URL}{uri}", params=params, **kwargs
                )
            else:
                # 其他错误：尝试更换账号信息后重试
                utils.logger.error(
                    f"[DouYinApiClient.get] 重试了5次: {uri} 请求，均失败了，尝试更换账号与IP再次发起重试"
                )
                await self.mark_account_invalid(self.account_info)
                await self.update_account_info()
                params = await self._pre_url_params(uri, params)
                return await self.request(
                    method="GET", url=f"{DOUYIN_API_URL}{uri}", params=params, **kwargs
                )

    async def post(
        self,
        uri: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        need_sign: bool = True,
        **kwargs,
    ):
        """
        POST请求方法
        自动处理签名和重试逻辑
        
        Args:
            uri: 请求URI
            params: 请求参数
            data: 请求体数据
            need_sign: 是否需要对请求参数进行签名
            **kwargs: 其他请求参数
            
        Returns:
            Dict: API响应JSON数据
        """
        try:
            # 如果需要签名，预处理参数
            if need_sign:
                params = await self._pre_url_params(uri, params)
            
            # 设置POST请求的特殊headers
            headers = copy.copy(self._headers)
            headers["Referer"] = "https://www.douyin.com/discover"
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            headers["X-Secsdk-Csrf-Token"] = "DOWNGRADE"
            
            return await self.request(
                method="POST",
                url=f"{DOUYIN_API_URL}{uri}",
                params=params,
                data=data,
                headers=headers,
                **kwargs,
            )
        except RetryError as e:
            # 获取原始异常
            original_exception = e.last_attempt.exception()
            exception_str = str(original_exception)
            traceback.print_exception(
                type(original_exception),
                original_exception,
                original_exception.__traceback__,
            )
            
            # 根据异常类型采取不同的处理策略
            account_related_errors = [
                "account blocked", "account unauthorized", "account not logged in", 
                "account error"
            ]
            
            if any(err in exception_str for err in account_related_errors):
                # 账号相关错误：立即标记账号无效并换账号
                utils.logger.error(
                    f"[DouYinApiClient.post] 账号相关错误: {exception_str}, 尝试更换账号与IP"
                )
                await self.mark_account_invalid(self.account_info)
                await self.update_account_info()
                # 重新设置headers
                headers = copy.copy(self._headers)
                headers["Referer"] = "https://www.douyin.com/discover"
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                headers["X-Secsdk-Csrf-Token"] = "DOWNGRADE"
                if need_sign:
                    params = await self._pre_url_params(uri, params)
                return await self.request(
                    method="POST",
                    url=f"{DOUYIN_API_URL}{uri}",
                    params=params,
                    data=data,
                    headers=headers,
                    **kwargs,
                )
            elif "rate limited" in exception_str:
                # 频率限制：等待更长时间后重试
                utils.logger.warning(
                    f"[DouYinApiClient.post] 请求频率受限，等待10秒后重试: {uri}"
                )
                await asyncio.sleep(10)
                # 重新设置headers
                headers = copy.copy(self._headers)
                headers["Referer"] = "https://www.douyin.com/discover"
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                headers["X-Secsdk-Csrf-Token"] = "DOWNGRADE"
                if need_sign:
                    params = await self._pre_url_params(uri, params)
                return await self.request(
                    method="POST",
                    url=f"{DOUYIN_API_URL}{uri}",
                    params=params,
                    data=data,
                    headers=headers,
                    **kwargs,
                )
            else:
                # 其他错误：尝试更换账号信息后重试
                utils.logger.error(
                    f"[DouYinApiClient.post] 重试了5次: {uri} 请求，均失败了，尝试更换账号与IP再次发起重试"
                )
                await self.mark_account_invalid(self.account_info)
                await self.update_account_info()
                # 重新设置headers
                headers = copy.copy(self._headers)
                headers["Referer"] = "https://www.douyin.com/discover"
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                headers["X-Secsdk-Csrf-Token"] = "DOWNGRADE"
                if need_sign:
                    params = await self._pre_url_params(uri, params)
                return await self.request(
                    method="POST",
                    url=f"{DOUYIN_API_URL}{uri}",
                    params=params,
                    data=data,
                    headers=headers,
                    **kwargs,
                )

    async def pong(self) -> bool:
        """
        测试账号是否可用
        通过检查登录状态来判断账号是否有效
        
        Returns:
            bool: True表示账号可用，False表示账号不可用
        """
        try:
            utils.logger.info(f"[DouYinApiClient.pong] ping user is logged in...")
            is_logged_in = await self.check_login_status_via_user_self()
            if is_logged_in:
                return True
        except Exception as e:
            utils.logger.error(
                f"[DouYinApiClient.pong] 登录检测失败,请检查cookies是否失效和被临时封禁，错误信息: {e}"
            )

        utils.logger.warning(
            f"[DouYinApiClient.pong] 登录检测失败,请检查cookies是否提取正确或者是否过期"
        )
        return False

    async def check_login_status_via_user_self(self) -> bool:
        """
        通过访问历史阅读接口来判断是否已登录
        
        未登录时返回: {"status_code": 8, "status_msg": "用户未登录"}
        已登录时返回: {"status_code": 0, "status_msg": "", "aweme_date": {...}}
        
        Returns:
            bool: True表示已登录，False表示未登录
        """
        params = {
            "max_cursor": 0,
            "count": 20,
        }

        try:
            response = await self.get(
                uri="/aweme/v1/web/history/read/",
                params=params,
            )

            # 判断登录状态：status_code == 0 表示已登录，status_code == 8 表示未登录
            status_code = response.get("status_code", -1)
            # 移除不必要的数据，只保留状态信息
            response.pop("aweme_list", None)
            response.pop("aweme_date", None)
            utils.logger.info(
                f"[DouYinApiClient.check_login_status_via_user_self] response: {response}"
            )
            return status_code == 0

        except Exception as e:
            utils.logger.error(
                f"[DouYinApiClient.check_login_status_via_user_self] 检查登录状态失败: {e}"
            )
            # 发生异常时认为未登录
            return False

    async def search_info_by_keyword(
        self,
        keyword: str,
        offset: int = 0,
        search_channel: SearchChannelType = SearchChannelType.GENERAL,
        sort_type: SearchSortType = SearchSortType.GENERAL,
        publish_time: PublishTimeType = PublishTimeType.UNLIMITED,
        search_id: str = "",
    ):
        """
        根据关键词搜索信息
        这是抖音搜索功能的核心API
        
        Args:
            keyword: 搜索关键字
            offset: 分页偏移量
            search_channel: 搜索渠道（综合/视频/用户/直播）
            sort_type: 排序类型（综合/最多点赞/最新发布）
            publish_time: 发布时间筛选（不限/一天内/一周内/半年内）
            search_id: 搜索ID（用于分页）
            
        Returns:
            Dict: API响应数据，包含搜索结果列表
        """
        query_params = {
            "search_channel": search_channel.value,
            "enable_history": "1",
            "keyword": keyword,
            "search_source": "tab_search",
            "query_correct_type": "1",
            "is_filter_search": "0",
            "from_group_id": "7378810571505847586",
            "offset": offset,
            "count": "10",
            "need_filter_settings": "1",
            "list_type": "multi",
            "search_id": search_id,
        }
        
        # 如果设置了排序或发布时间筛选，添加过滤参数
        if (
            sort_type.value != SearchSortType.GENERAL.value
            or publish_time.value != PublishTimeType.UNLIMITED.value
        ):
            query_params["filter_selected"] = json.dumps(
                {
                    "sort_type": str(sort_type.value),
                    "publish_time": str(publish_time.value),
                },
                separators=(",", ":"),
            )
            query_params["is_filter_search"] = 1
            query_params["search_source"] = "tab_search"
        
        return await self.get("/aweme/v1/web/general/search/single/", query_params)

    async def get_video_by_id(self, aweme_id: str) -> Optional[DouyinAweme]:
        """
        根据视频ID获取视频详情
        
        Args:
            aweme_id: 视频ID（aweme_id）
            
        Returns:
            Optional[DouyinAweme]: 视频模型对象，如果获取失败返回None
        """
        params = {
            "aweme_id": aweme_id,
            "verifyFp": self.common_verify_params.verify_fp,
            "fp": self.common_verify_params.verify_fp,
        }
        params.update(self._verify_params)
        
        # 详情接口需要特殊的headers
        headers = copy.copy(self._headers)
        if "Origin" in headers:
            del headers["Origin"]
        
        res = await self.get("/aweme/v1/web/aweme/detail/", params, headers=headers)
        aweme_detail = res.get("aweme_detail", {})
        if aweme_detail:
            return self._extractor.extract_aweme_from_dict(aweme_detail)
        return None

    async def get_aweme_comments(
        self, aweme_id: str, cursor: int = 0
    ) -> Tuple[List[DouyinAwemeComment], Dict]:
        """
        获取视频的评论列表
        
        Args:
            aweme_id: 视频ID
            cursor: 分页游标，0表示第一页
            
        Returns:
            Tuple[List[DouyinAwemeComment], Dict]: 
                - 评论模型对象列表
                - 响应元数据（包含has_more、cursor等信息）
        """
        uri = "/aweme/v1/web/comment/list/"
        params = {
            "aweme_id": aweme_id,
            "cursor": cursor,
            "count": 20,
            "item_type": 0,
            "verifyFp": self.common_verify_params.verify_fp,
            "fp": self.common_verify_params.verify_fp,
        }
        params.update(self._verify_params)
        
        # 设置Referer，模拟从搜索页面进入
        keywords = request_keyword_var.get() or ""
        referer_url = (
            "https://www.douyin.com/search/"
            + keywords
            + "?aid=3a3cec5a-9e27-4040-b6aa-ef548c2c1138&publish_time=0&sort_type=0&source=search_history&type=general"
        )
        headers = copy.copy(self._headers)
        headers["Referer"] = urllib.parse.quote(referer_url, safe=":/")
        
        res = await self.get(uri, params, headers=headers)

        # 提取评论数据并转换为模型对象
        comments_data = res.get("comments", [])
        comments = self._extractor.extract_comments_from_dict(aweme_id, comments_data)

        # 返回评论列表和元数据
        return comments, res

    async def get_sub_comments(
        self, comment_id: str, cursor: int = 0, aweme_id: str = ""
    ) -> Tuple[List[DouyinAwemeComment], Dict]:
        """
        获取子评论（评论的回复）
        
        Args:
            comment_id: 父评论ID
            cursor: 分页游标
            aweme_id: 视频ID（用于构建评论模型）
            
        Returns:
            Tuple[List[DouyinAwemeComment], Dict]: 
                - 子评论模型对象列表
                - 响应元数据
        """
        uri = "/aweme/v1/web/comment/list/reply/"
        params = {
            "comment_id": comment_id,
            "cursor": cursor,
            "count": 20,
            "item_type": 0,
            "verifyFp": self.common_verify_params.verify_fp,
            "fp": self.common_verify_params.verify_fp,
        }
        params.update(self._verify_params)
        
        # 设置Referer
        keywords = request_keyword_var.get() or ""
        referer_url = (
            "https://www.douyin.com/search/"
            + keywords
            + "?aid=3a3cec5a-9e27-4040-b6aa-ef548c2c1138&publish_time=0&sort_type=0&source=search_history&type=general"
        )
        headers = copy.copy(self._headers)
        headers["Referer"] = urllib.parse.quote(referer_url, safe=":/")
        
        res = await self.get(uri, params, headers=headers)

        # 提取子评论数据
        comments_data = res.get("comments", [])
        comments = (
            self._extractor.extract_comments_from_dict(aweme_id, comments_data)
            if aweme_id
            else []
        )

        return comments, res

    async def get_user_info(self, sec_user_id: str) -> Optional[DouyinCreator]:
        """
        获取指定用户（创作者）的信息
        
        Args:
            sec_user_id: 用户的sec_user_id（抖音的用户标识）
            
        Returns:
            Optional[DouyinCreator]: 创作者模型对象，如果获取失败返回None
        """
        uri = "/aweme/v1/web/user/profile/other/"
        params = {
            "sec_user_id": sec_user_id,
            "publish_video_strategy_type": 2,
            "personal_center_strategy": 1,
            "verifyFp": self.common_verify_params.verify_fp,
            "fp": self.common_verify_params.verify_fp,
        }
        res = await self.get(uri, params)
        user_info = res.get("user", {})
        if user_info:
            return self._extractor.extract_creator_from_dict(user_info)
        return None

    async def get_user_aweme_posts(
        self, sec_user_id: str, max_cursor: str = "0"
    ) -> Dict:
        """
        获取指定用户的所有视频（作品列表）
        
        Args:
            sec_user_id: 用户的sec_user_id
            max_cursor: 分页游标，用于获取下一页数据
            
        Returns:
            Dict: API响应数据，包含视频列表和分页信息
        """
        uri = "/aweme/v1/web/aweme/post/"
        params = {
            "sec_user_id": sec_user_id,
            "count": 18,
            "max_cursor": max_cursor,
            "locate_query": "false",
            "publish_video_strategy_type": 2,
            "verifyFp": self.common_verify_params.verify_fp,
            "fp": self.common_verify_params.verify_fp,
        }
        return await self.get(uri, params)

    async def get_homefeed_aweme_list(
        self,
        tag_id: HomeFeedTagIdType = HomeFeedTagIdType.ALL,
        refresh_index: int = 0,
        count: int = 20,
    ):
        """
        获取抖音首页推荐视频列表（homefeed信息流）
        
        Args:
            tag_id: 标签类型（全部/知识/体育/汽车等）
            refresh_index: 刷新索引，用于分页
            count: 每次获取的视频数量
            
        Returns:
            Dict: API响应数据，包含推荐视频列表
        """
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "module_id": "3003101",
            "count": count,
            "filterGids": "",
            "presented_ids": "",
            "refresh_index": refresh_index,
            "refer_id": "",
            "refer_type": "10",
            "awemePcRecRawData": '{"is_xigua_user":0,"is_client":false}',
            "Seo-Flag": "0",
            "install_time": "1749390216",
            "tag_id": tag_id.value,
            "use_lite_type": "0",
            "xigua_user": "0",
            "pc_client_type": "1",
            "pc_libra_divert": "Mac",
            "update_version_code": "170400",
            "support_h265": "1",
            "support_dash": "1",
            "version_code": "170400",
            "version_name": "17.4.0",
            "cookie_enabled": "true",
            "screen_width": "2560",
            "screen_height": "1440",
            "browser_language": "en",
            "browser_platform": "MacIntel",
            "browser_name": "Chrome",
            "browser_version": "135.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "135.0.0.0",
            "os_name": "Mac OS",
            "os_version": "10.15.7",
            "cpu_core_num": "10",
            "device_memory": "8",
            "platform": "PC",
            "downlink": "10",
            "effective_type": "4g",
            "round_trip_time": "100",
        }

        # 首页推荐接口使用POST请求，且不需要签名
        return await self.post("/aweme/v1/web/module/feed/", params, need_sign=False)

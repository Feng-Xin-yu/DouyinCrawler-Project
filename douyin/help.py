# -*- coding: utf-8 -*-
"""
抖音爬虫辅助函数
提供获取通用验证参数的功能，包括ms_token、webid、verify_fp等
"""

import random
import time

import httpx
from pydantic import BaseModel, Field

from constant.douyin import (
    DOUYIN_FIXED_USER_AGENT,
    DOUYIN_MS_TOKEN_REQ_STR_DATA,
    DOUYIN_MS_TOKEN_REQ_URL,
    DOUYIN_WEBID_REQ_URL
)
from pkg.async_http_client import AsyncHTTPClient
from pkg.tools import utils


class CommonVerifyParams(BaseModel):
    """
    通用验证参数模型
    包含抖音请求所需的各种验证参数
    """
    ms_token: str = Field(..., title="ms_token", description="ms_token验证参数")
    webid: str = Field(..., title="webid", description="webid设备标识")
    verify_fp: str = Field(..., title="verify_fp", description="verify_fp验证参数")
    s_v_web_id: str = Field(..., title="s_v_web_id", description="s_v_web_id验证参数")


async def get_common_verify_params(user_agent: str) -> CommonVerifyParams:
    """
    获取通用验证参数
    这是抖音请求必需的参数，用于验证请求的合法性
    
    Args:
        user_agent: User-Agent字符串
        
    Returns:
        CommonVerifyParams: 通用验证参数对象
    """
    utils.logger.info(
        f"[get_common_verify_params] Start to get common verify params"
    )
    token_manager = TokenManager(user_agent)
    ms_token = await token_manager.get_msToken()
    webid = await token_manager.gen_webid()
    verify_fp = VerifyFpManager.gen_verify_fp()
    s_v_web_id = VerifyFpManager.gen_s_v_web_id()
    utils.logger.info(
        f"[get_common_verify_params] Get ms_token: {ms_token[:20]}..., "
        f"webid: {webid}, verify_fp: {verify_fp[:20]}..., s_v_web_id: {s_v_web_id[:20]}..."
    )

    return CommonVerifyParams(
        ms_token=ms_token, webid=webid, verify_fp=verify_fp, s_v_web_id=s_v_web_id
    )


def get_web_id():
    """
    生成随机的webid（备用方法）
    当无法从API获取webid时使用
    
    Returns:
        str: 生成的webid字符串
    """
    def e(t):
        if t is not None:
            return str(t ^ (int(16 * random.random()) >> (t // 4)))
        else:
            return "".join(
                [
                    str(int(1e7)),
                    "-",
                    str(int(1e3)),
                    "-",
                    str(int(4e3)),
                    "-",
                    str(int(8e3)),
                    "-",
                    str(int(1e11)),
                ]
            )

    web_id = "".join(e(int(x)) if x in "018" else x for x in e(None))
    return web_id.replace("-", "")[:19]


class TokenManager:
    """
    Token管理器
    负责生成和获取msToken和webid
    参考：https://github.com/johnserf-seed/f2
    """
    
    def __init__(self, user_agent: str):
        """
        初始化Token管理器
        
        Args:
            user_agent: User-Agent字符串
        """
        self._user_agent = user_agent

    async def gen_real_msToken(self) -> str:
        """
        生成真实的msToken
        通过调用抖音的API获取真实的msToken
        
        Returns:
            str: msToken字符串
            
        Raises:
            Exception: 如果获取失败或格式不正确
        """
        async with AsyncHTTPClient() as client:
            post_data = {
                "magic": 538969122,
                "version": 1,
                "dataType": 8,
                "strData": DOUYIN_MS_TOKEN_REQ_STR_DATA,
                "tspFromClient": utils.get_current_timestamp(),
                "url": 0,
            }
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": self._user_agent,
            }
            response = await client.post(
                DOUYIN_MS_TOKEN_REQ_URL, json=post_data, headers=headers
            )
            ms_token = str(httpx.Cookies(response.cookies).get("msToken"))
            if len(ms_token) not in [120, 128]:
                raise Exception(f"获取msToken内容不符合要求: {ms_token}")
            return ms_token

    @classmethod
    def gen_fake_msToken(cls) -> str:
        """
        生成假的msToken（备用方法）
        当无法获取真实msToken时使用
        
        Returns:
            str: 假的msToken字符串
        """
        false_ms_token = utils.get_random_str(126) + "=="
        return false_ms_token

    async def get_msToken(self) -> str:
        """
        获取msToken
        优先尝试获取真实的msToken，失败则使用假的msToken
        
        Returns:
            str: msToken字符串
        """
        try:
            return await self.gen_real_msToken()
        except Exception as e:
            utils.logger.warning(
                f"gen_real_msToken error: {e}, return a fake msToken"
            )
            return self.gen_fake_msToken()

    async def gen_webid(self) -> str:
        """
        生成个性化追踪webid
        通过调用抖音的API获取webid
        
        Returns:
            str: webid字符串
        """
        async with AsyncHTTPClient() as client:
            post_data = {
                "app_id": 6383,
                "referer": f"https://www.douyin.com/",
                "url": "https://www.douyin.com/",
                "user_agent": self._user_agent,
                "user_unique_id": "",
            }
            headers = {
                "User-Agent": self._user_agent,
                "Content-Type": "application/json; charset=UTF-8",
                "Referer": "https://www.douyin.com/",
            }
            try:
                response = await client.post(
                    DOUYIN_WEBID_REQ_URL, json=post_data, headers=headers
                )
                webid = response.json().get("web_id")
                if not webid:
                    raise Exception("获取webid失败")
                return webid
            except Exception as e:
                utils.logger.warning(
                    f"gen_webid error: {e}, return a random webid"
                )
                return get_web_id()


class VerifyFpManager:
    """
    VerifyFp管理器
    负责生成verifyFp和s_v_web_id
    参考：https://github.com/johnserf-seed/f2
    """
    
    @classmethod
    def gen_verify_fp(cls) -> str:
        """
        生成verifyFp验证参数
        
        Returns:
            str: verifyFp字符串
        """
        base_str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        t = len(base_str)
        milliseconds = int(round(time.time() * 1000))
        base36 = ""
        while milliseconds > 0:
            remainder = milliseconds % 36
            if remainder < 10:
                base36 = str(remainder) + base36
            else:
                base36 = chr(ord("a") + remainder - 10) + base36
            milliseconds = int(milliseconds / 36)
        r = base36
        o = [""] * 36
        o[8] = o[13] = o[18] = o[23] = "_"
        o[14] = "4"

        for i in range(36):
            if not o[i]:
                n = 0 or int(random.random() * t)
                if i == 19:
                    n = 3 & n | 8
                o[i] = base_str[n]

        return "verify_" + r + "_" + "".join(o)

    @classmethod
    def gen_s_v_web_id(cls) -> str:
        """
        生成s_v_web_id验证参数
        
        Returns:
            str: s_v_web_id字符串
        """
        return cls.gen_verify_fp()

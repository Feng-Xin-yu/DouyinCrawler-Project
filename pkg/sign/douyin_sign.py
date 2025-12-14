# -*- coding: utf-8 -*-
"""
抖音签名逻辑
提供抖音请求签名的实现，支持Playwright和JavaScript两种方式
"""

from abc import ABC, abstractmethod
from pathlib import Path

import execjs
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

from pkg.sign.sign_model import DouyinSignRequest, DouyinSignResponse
from pkg.tools import utils

# 签名类型常量
DOUYIN_JAVASCRIPT_SIGN = "javascript"
DOUYIN_PLAYWRIGHT_SIGN = "playwright"


class AbstractDouyinSign(ABC):
    """
    抖音签名抽象基类
    定义签名方法的统一接口
    """
    
    @abstractmethod
    async def sign(
        self, req_data: DouyinSignRequest, force_init: bool = False
    ) -> DouyinSignResponse:
        """
        生成签名
        
        Args:
            req_data: 签名请求数据
            force_init: 是否强制重新初始化
            
        Returns:
            DouyinSignResponse: 签名响应数据
        """
        raise NotImplementedError("子类必须实现 sign 方法")


class DouyinJavascriptSign(AbstractDouyinSign):
    """
    抖音JavaScript签名实现
    通过执行JavaScript代码生成签名
    """
    
    def __init__(self):
        """
        初始化JavaScript签名器
        加载并编译JavaScript签名代码
        """
        # 获取项目根目录（pkg/sign/douyin_sign.py -> pkg -> 项目根目录）
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / 'pkg' / 'js' / 'douyin.js'
        
        # 如果找不到文件，尝试从当前工作目录查找
        if not script_path.exists():
            # 尝试从当前工作目录查找
            cwd_script_path = Path('pkg/js/douyin.js')
            if cwd_script_path.exists():
                script_path = cwd_script_path.resolve()
            else:
                # 最后尝试从当前文件位置查找
                current_dir = Path(__file__).parent
                script_path = current_dir.parent.parent / 'pkg' / 'js' / 'douyin.js'
        
        if not script_path.exists():
            error_msg = f"[DouyinJavascriptSign] JS file not found: {script_path}"
            utils.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            script_content = script_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            script_content = script_path.read_text(encoding='gbk')
        except Exception as e:
            utils.logger.error(f"[DouyinJavascriptSign] Failed to load JS file {script_path}: {e}")
            raise
        
        # 编译JavaScript代码
        try:
            self.douyin_sign_obj = execjs.compile(script_content)
            utils.logger.info("[DouyinJavascriptSign] JavaScript signature code loaded successfully")
        except Exception as e:
            utils.logger.error(f"[DouyinJavascriptSign] Failed to compile JS code: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
    async def sign(
        self, req: DouyinSignRequest, force_init: bool = False
    ) -> DouyinSignResponse:
        """
        抖音请求签名JavaScript版本
        如果发生异常默认重试3次，每次间隔500ms
        
        Args:
            req: 签名请求数据
            force_init: 是否强制重新初始化（JavaScript方式不需要）
            
        Returns:
            DouyinSignResponse: 签名响应数据
        """
        try:
            # 调用JavaScript函数生成a_bogus
            a_bogus = self.douyin_sign_obj.call(
                "get_abogus", req.query_params, "", req.user_agent
            )
            # 返回响应，设置a_bogus字段
            return DouyinSignResponse(a_bogus=a_bogus, isok=True, msg="OK!")
        except Exception as e:
            utils.logger.error(f"[DouyinJavascriptSign.sign] Failed to generate signature: {e}")
            raise


class DouyinPlaywrightSign(AbstractDouyinSign):
    """
    抖音Playwright签名实现
    通过Playwright调用浏览器环境中的JavaScript函数生成签名
    
    注意：此方式需要浏览器环境，资源消耗较大
    """
    
    def __init__(self):
        """
        初始化Playwright签名器
        """
        self._playwright_manager = None
        utils.logger.warning(
            "[DouyinPlaywrightSign] Playwright mode requires browser environment, "
            "consider using JavaScript mode for better performance"
        )

    async def _get_playwright_manager(self):
        """
        获取Playwright管理器（延迟初始化）
        """
        if self._playwright_manager is None:
            # 如果使用Playwright方式，需要初始化浏览器环境
            # 这里暂时不支持，建议使用JavaScript方式
            raise NotImplementedError(
                "Playwright mode is not fully supported in merged version. "
                "Please use JavaScript mode instead."
            )
        return self._playwright_manager

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
    async def sign(
        self, req: DouyinSignRequest, force_init: bool = False
    ) -> DouyinSignResponse:
        """
        抖音请求签名playwright版本
        如果发生异常默认重试3次，每次间隔500ms
        
        Args:
            req: 签名请求数据
            force_init: 是否强制重新初始化页面
            
        Returns:
            DouyinSignResponse: 签名响应数据
        """
        # Playwright方式暂时不支持，建议使用JavaScript方式
        raise NotImplementedError(
            "Playwright mode is not fully supported in merged version. "
            "Please use JavaScript mode instead. "
            "You can set SIGN_TYPE=javascript in config."
        )


class DouyinSignFactory:
    """
    抖音签名工厂类
    根据签名类型创建相应的签名器实例
    """
    
    @staticmethod
    def get_sign(sign_type: str) -> AbstractDouyinSign:
        """
        根据签名类型获取签名器实例
        
        Args:
            sign_type: 签名类型（playwright或javascript）
            
        Returns:
            AbstractDouyinSign: 签名器实例
            
        Raises:
            NotImplementedError: 如果签名类型不支持
        """
        if sign_type == DOUYIN_PLAYWRIGHT_SIGN:
            utils.logger.warning(
                "[DouyinSignFactory] Playwright mode is not fully supported, "
                "falling back to JavaScript mode"
            )
            # 暂时不支持Playwright，回退到JavaScript
            return DouyinJavascriptSign()
        elif sign_type == DOUYIN_JAVASCRIPT_SIGN:
            return DouyinJavascriptSign()
        else:
            raise NotImplementedError(f"不支持的签名类型: {sign_type}")


class DouyinSignLogic:
    """
    抖音签名逻辑类
    封装签名器的调用逻辑，提供统一的签名接口
    """
    
    def __init__(self, sign_type: str = DOUYIN_JAVASCRIPT_SIGN):
        """
        初始化签名逻辑
        
        Args:
            sign_type: 签名类型（playwright或javascript），默认使用javascript
        """
        self.sign_type = sign_type
        self.sign_server = DouyinSignFactory.get_sign(sign_type)
        utils.logger.info(f"[DouyinSignLogic] Initialized with sign type: {sign_type}")

    async def sign(self, req_data: DouyinSignRequest) -> DouyinSignResponse:
        """
        生成签名
        如果签名失败，会尝试强制重新初始化后重试
        
        Args:
            req_data: 签名请求数据
            
        Returns:
            DouyinSignResponse: 签名响应数据
        """
        try:
            return await self.sign_server.sign(req_data)
        except RetryError:
            # 如果重试失败，尝试强制重新初始化
            utils.logger.warning(
                "[DouyinSignLogic.sign] Retry failed, attempting force reinit"
            )
            return await self.sign_server.sign(req_data, force_init=True)

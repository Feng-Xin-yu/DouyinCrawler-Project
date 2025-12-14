# -*- coding: utf-8 -*-
"""
抖音爬虫核心
协调各个组件，实现完整的爬虫功能
这是爬虫的主控制器，负责初始化和启动爬虫
"""

import asyncio
from datetime import datetime
from typing import Optional

import config
import constant
from base.base_crawler import AbstractCrawler
from constant.douyin import DOUYIN_FIXED_USER_AGENT
from pkg.account_pool.pool import AccountWithIpPoolManager
from pkg.proxy.proxy_ip_pool import ProxyIpPool, create_ip_pool
from pkg.tools import utils
from var import crawler_type_var

from .client import DouYinApiClient
from .help import get_common_verify_params

from .handlers import SearchHandler, DetailHandler, CreatorHandler, HomefeedHandler
from .processors import AwemeProcessor, CommentProcessor
from repo.checkpoint import create_checkpoint_manager
from repo.checkpoint.checkpoint_store import CheckpointRepoManager


class DouYinCrawler(AbstractCrawler):
    """
    抖音爬虫主类
    继承自AbstractCrawler，实现抖音平台的爬虫功能
    
    设计思路：
    1. 使用依赖注入模式，将各个组件组合在一起
    2. 通过Handler处理不同类型的爬取任务
    3. 通过Processor处理爬取到的数据
    4. 使用信号量控制并发数量
    """
    
    def __init__(self) -> None:
        """
        初始化抖音爬虫
        创建各个组件实例，使用依赖注入模式
        """
        # 创建API客户端
        self.dy_client = DouYinApiClient()
        
        # 创建断点管理器（文件存储）
        self.checkpoint_manager: CheckpointRepoManager = create_checkpoint_manager()

        # 限制并发数的信号量
        # 使用信号量控制同时进行的爬取任务数量，避免对平台造成过大压力
        self.crawler_aweme_task_semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        self.crawler_comment_semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)

        # 初始化数据处理器
        self.aweme_processor = AwemeProcessor(
            self.dy_client,
            self.crawler_aweme_task_semaphore,
            checkpoint_manager=self.checkpoint_manager,
        )
        self.comment_processor = CommentProcessor(
            self.dy_client,
            self.crawler_comment_semaphore,
            checkpoint_manager=self.checkpoint_manager,
        )

        # 初始化处理器
        self.search_handler = SearchHandler(
            self.dy_client,
            checkpoint_manager=self.checkpoint_manager,
            aweme_processor=self.aweme_processor,
            comment_processor=self.comment_processor,
        )
        self.detail_handler = DetailHandler(
            self.dy_client,
            checkpoint_manager=self.checkpoint_manager,
            aweme_processor=self.aweme_processor,
            comment_processor=self.comment_processor,
        )
        self.creator_handler = CreatorHandler(
            self.dy_client,
            checkpoint_manager=self.checkpoint_manager,
            aweme_processor=self.aweme_processor,
            comment_processor=self.comment_processor,
        )
        self.homefeed_handler = HomefeedHandler(
            self.dy_client,
            checkpoint_manager=self.checkpoint_manager,
            aweme_processor=self.aweme_processor,
            comment_processor=self.comment_processor,
        )

    async def async_initialize(self):
        """
        异步初始化
        在爬虫启动前进行初始化工作，包括：
        1. 获取通用验证参数（ms_token、webid等）
        2. 初始化账号池和代理IP池
        3. 更新账号信息
        4. 设置爬虫类型
        """
        from pkg.tools.output_formatter import OutputFormatter
        
        # 显示启动信息
        crawler_type_name = {
            constant.CRALER_TYPE_SEARCH: "关键词搜索",
            constant.CRALER_TYPE_DETAIL: "视频详情",
            constant.CRALER_TYPE_CREATOR: "创作者主页",
            constant.CRALER_TYPE_HOMEFEED: "首页推荐",
        }.get(config.CRAWLER_TYPE, config.CRAWLER_TYPE)
        
        config_info = {
            "爬取类型": crawler_type_name,
            "存储方式": config.SAVE_DATA_OPTION.upper(),
            "断点续爬": "已启用" if config.ENABLE_CHECKPOINT else "未启用",
            "并发数量": config.MAX_CONCURRENCY_NUM,
            "请求间隔": f"{config.CRAWLER_TIME_SLEEP}秒",
        }
        OutputFormatter.print_crawler_start(crawler_type_name, config_info)
        
        utils.logger.info("[DouYinCrawler.async_initialize] 初始化中...")
        
        # 获取通用验证参数
        self.dy_client.common_verify_params = await get_common_verify_params(
            DOUYIN_FIXED_USER_AGENT
        )
        OutputFormatter.print_success("验证参数获取成功")

        # 账号池和IP池的初始化
        proxy_ip_pool: Optional[ProxyIpPool] = None
        if config.ENABLE_IP_PROXY:
            OutputFormatter.print_info("初始化代理IP池...")
            proxy_ip_pool = await create_ip_pool(
                config.IP_PROXY_POOL_COUNT, enable_validate_ip=True
            )
            OutputFormatter.print_success(f"代理IP池初始化成功 (数量: {config.IP_PROXY_POOL_COUNT})")

        # 初始化账号池
        OutputFormatter.print_info("初始化账号池...")
        account_with_ip_pool = AccountWithIpPoolManager(
            platform_name=constant.DOUYIN_PLATFORM_NAME,
            account_save_type=config.ACCOUNT_POOL_SAVE_TYPE,
            proxy_ip_pool=proxy_ip_pool,
        )
        await account_with_ip_pool.async_initialize()
        
        account_count = len(account_with_ip_pool._account_list)
        OutputFormatter.print_success(f"账号池初始化成功 (账号数量: {account_count})")

        # 将账号池赋值给客户端
        self.dy_client.account_with_ip_pool = account_with_ip_pool
        # 更新账号信息（获取第一个可用账号）
        await self.dy_client.update_account_info()
        
        if self.dy_client.account_info:
            account_name = self.dy_client.account_info.account.account_name
            OutputFormatter.print_account_info(account_name, "正常")

        # 设置爬虫类型到上下文变量
        crawler_type_var.set(config.CRAWLER_TYPE)
        
        OutputFormatter.print_success("爬虫初始化完成\n")

    async def start(self) -> None:
        """
        启动爬虫
        根据配置的爬取类型，调用相应的Handler执行爬取任务
        """
        # 根据爬取类型选择相应的Handler
        if config.CRAWLER_TYPE == constant.CRALER_TYPE_SEARCH:
            # 关键词搜索爬取
            await self.search_handler.handle()
        elif config.CRAWLER_TYPE == constant.CRALER_TYPE_DETAIL:
            # 视频详情爬取
            await self.detail_handler.handle()
        elif config.CRAWLER_TYPE == constant.CRALER_TYPE_CREATOR:
            # 创作者主页爬取
            await self.creator_handler.handle()
        elif config.CRAWLER_TYPE == constant.CRALER_TYPE_HOMEFEED:
            # 首页推荐爬取
            await self.homefeed_handler.handle()
        else:
            raise NotImplementedError(
                f"[DouYinCrawler.start] Not support crawler type: {config.CRAWLER_TYPE}"
            )
        from pkg.tools.output_formatter import OutputFormatter
        
        OutputFormatter.print_crawler_summary({
            "状态": "爬取完成",
            "时间": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        })
        utils.logger.info("[DouYinCrawler.start] Douyin Crawler finished ...")
    
    async def cleanup(self):
        """
        清理资源
        关闭HTTP客户端连接等
        """
        if self.dy_client:
            await self.dy_client.cleanup()
        utils.logger.info("[DouYinCrawler.cleanup] Resources cleaned up")

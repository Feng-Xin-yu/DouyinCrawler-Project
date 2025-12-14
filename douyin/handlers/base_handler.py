# -*- coding: utf-8 -*-
"""
处理器基类
定义所有处理器的统一接口
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import DouYinApiClient
    # from repo.checkpoint.checkpoint_store import CheckpointRepoManager
    # from ..processors.aweme_processor import AwemeProcessor
    # from ..processors.comment_processor import CommentProcessor


class BaseHandler(ABC):
    """
    处理器基类
    所有具体的处理器都必须继承此类并实现handle方法
    
    设计思路：
    1. 使用抽象基类确保所有处理器都有统一的接口
    2. 通过依赖注入传入所需的组件（客户端、处理器等）
    3. handle方法是处理器的核心，负责执行具体的爬取逻辑
    """
    
    def __init__(
        self,
        dy_client: "DouYinApiClient",
        checkpoint_manager=None,
        aweme_processor=None,
        comment_processor=None,
    ):
        """
        初始化基础处理器
        
        Args:
            dy_client: 抖音API客户端
            checkpoint_manager: 断点管理器（用于断点续爬）
            aweme_processor: 视频数据处理器
            comment_processor: 评论数据处理器
        """
        self.dy_client = dy_client
        self.checkpoint_manager = checkpoint_manager
        self.aweme_processor = aweme_processor
        self.comment_processor = comment_processor

    @abstractmethod
    async def handle(self) -> None:
        """
        处理爬取任务
        这是处理器的核心方法，每个具体的处理器都必须实现此方法
        
        Returns:
            None
        """
        raise NotImplementedError("子类必须实现 handle 方法")

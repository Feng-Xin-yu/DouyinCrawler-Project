# -*- coding: utf-8 -*-
"""
详情处理器
处理指定视频ID的详情爬取任务
"""

from typing import List, TYPE_CHECKING

import config
import constant
from model.m_checkpoint import Checkpoint
from pkg.tools import utils
from .base_handler import BaseHandler

if TYPE_CHECKING:
    from ..client import DouYinApiClient
    # from repo.checkpoint.checkpoint_store import CheckpointRepoManager
    from ..processors.aweme_processor import AwemeProcessor
    from ..processors.comment_processor import CommentProcessor


class DetailHandler(BaseHandler):
    """
    详情处理器
    处理指定视频ID的详情爬取任务
    
    主要功能：
    1. 根据配置的视频ID列表爬取视频详情
    2. 获取视频评论
    """
    
    def __init__(
        self,
        dy_client: "DouYinApiClient",
        checkpoint_manager=None,
        aweme_processor=None,
        comment_processor=None,
    ):
        """
        初始化详情处理器
        
        Args:
            dy_client: 抖音API客户端
            checkpoint_manager: 断点管理器（用于断点续爬）
            aweme_processor: 视频数据处理器
            comment_processor: 评论数据处理器
        """
        super().__init__(
            dy_client,
            checkpoint_manager=checkpoint_manager,
            aweme_processor=aweme_processor,
            comment_processor=comment_processor,
        )

    async def handle(self) -> None:
        """
        处理详情爬取任务
        
        Returns:
            None
        """
        await self.get_specified_awemes()

    async def get_specified_awemes(self):
        """
        获取指定视频的详情和评论信息
        
        Returns:
            None
        """
        utils.logger.info(
            "[DetailHandler.get_specified_awemes] Begin get douyin specified awemes"
        )

        # 获取配置的视频ID列表
        aweme_id_list = config.DY_SPECIFIED_ID_LIST
        if not aweme_id_list:
            utils.logger.error(
                "[DetailHandler.get_specified_awemes] DY_SPECIFIED_ID_LIST is empty, please configure it"
            )
            return

        utils.logger.info(
            f"[DetailHandler.get_specified_awemes] Will crawl {len(aweme_id_list)} awemes"
        )

        # 断点续爬
        checkpoint = Checkpoint(platform=constant.DOUYIN_PLATFORM_NAME, mode=constant.CRALER_TYPE_DETAIL)
        if config.ENABLE_CHECKPOINT and self.checkpoint_manager:
            lastest_checkpoint = await self.checkpoint_manager.load_checkpoint(
                platform=constant.DOUYIN_PLATFORM_NAME,
                mode=constant.CRALER_TYPE_DETAIL,
                checkpoint_id=config.SPECIFIED_CHECKPOINT_ID,
            )
            if lastest_checkpoint:
                checkpoint = lastest_checkpoint
                utils.logger.info(
                    f"[DetailHandler.get_specified_awemes] Load last checkpoint: {lastest_checkpoint.id}"
                )
            else:
                checkpoint = await self.checkpoint_manager.save_checkpoint(checkpoint)

        # 使用processor批量处理，带断点
        processed_aweme_ids = await self.aweme_processor.batch_get_aweme_list_from_ids(
            aweme_id_list, checkpoint_id=checkpoint.id if config.ENABLE_CHECKPOINT else ""
        )
        await self.comment_processor.batch_get_aweme_comments(
            processed_aweme_ids, checkpoint_id=checkpoint.id if config.ENABLE_CHECKPOINT else ""
        )

        utils.logger.info(
            "[DetailHandler.get_specified_awemes] Get douyin specified awemes finished ..."
        )

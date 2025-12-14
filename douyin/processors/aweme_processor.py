# -*- coding: utf-8 -*-
"""
视频数据处理器
负责处理视频数据的获取、存储等操作
"""

import asyncio
from typing import List, Optional, TYPE_CHECKING

from model.m_douyin import DouyinAweme
from pkg.tools import utils
from repo.platform_save_data import douyin as douyin_store
from ..exception import DataFetchError

if TYPE_CHECKING:
    from ..client import DouYinApiClient
    # from repo.checkpoint.checkpoint_store import CheckpointRepoManager


class AwemeProcessor:
    """
    视频数据处理器
    负责处理视频数据的获取、存储等操作
    
    主要功能：
    1. 获取视频详情
    2. 批量处理视频列表
    3. 与断点管理器交互，支持断点续爬
    """
    
    def __init__(
        self,
        dy_client: "DouYinApiClient",
        crawler_aweme_task_semaphore: asyncio.Semaphore,
        checkpoint_manager=None,
    ):
        """
        初始化视频处理器
        
        Args:
            dy_client: 抖音API客户端
            checkpoint_manager: 断点管理器（用于断点续爬）
            crawler_aweme_task_semaphore: 信号量，用于控制并发数量
        """
        self.dy_client = dy_client
        self.checkpoint_manager = checkpoint_manager
        self.crawler_aweme_task_semaphore = crawler_aweme_task_semaphore

    async def get_aweme_detail_async_task(
        self,
        aweme_id: str,
        checkpoint_id: str = "",
    ) -> Optional[DouyinAweme]:
        """
        异步获取视频详情
        
        Args:
            aweme_id: 视频ID
            checkpoint_id: 检查点ID（用于断点续爬）
            
        Returns:
            Optional[DouyinAweme]: 视频模型对象，如果获取失败返回None
        """
        aweme = None
        # 使用信号量控制并发
        async with self.crawler_aweme_task_semaphore:
            try:
                # 调用API获取视频详情
                aweme = await self.dy_client.get_video_by_id(aweme_id)
                if aweme:
                    # 保存视频数据到存储层
                    await douyin_store.update_douyin_aweme(aweme)
                    utils.logger.info(
                        f"[AwemeProcessor.get_aweme_detail_async_task] Successfully get aweme detail: {aweme_id}"
                    )
                    return aweme
                else:
                    utils.logger.warning(
                        f"[AwemeProcessor.get_aweme_detail_async_task] have not found aweme detail aweme_id:{aweme_id}"
                    )

            except DataFetchError as ex:
                utils.logger.error(
                    f"[AwemeProcessor.get_aweme_detail_async_task] Get aweme detail error: {ex}"
                )
                return None

            except KeyError as ex:
                utils.logger.error(
                    f"[AwemeProcessor.get_aweme_detail_async_task] have not found aweme detail aweme_id:{aweme_id}, err: {ex}"
                )
                return None

            finally:
                # 更新断点信息（如果启用了断点续爬）
                if checkpoint_id and self.checkpoint_manager:
                    is_success_crawled = aweme is not None
                    await self.checkpoint_manager.update_note_to_checkpoint(
                        checkpoint_id=checkpoint_id,
                        note_id=aweme_id,
                        is_success_crawled=is_success_crawled,
                        is_success_crawled_comments=False,
                        current_note_comment_cursor=None,
                    )

    async def batch_get_aweme_list_from_ids(
        self, aweme_ids: List[str], checkpoint_id: str = ""
    ) -> List[str]:
        """
        批量获取视频列表
        并发获取指定ID列表的视频详情并保存数据
        
        Args:
            aweme_ids: 视频ID列表
            checkpoint_id: 检查点ID（用于断点续爬）
            
        Returns:
            List[str]: 成功处理的视频ID列表
        """
        task_list, processed_aweme_ids = [], []
        
        for aweme_id in aweme_ids:
            # 检查是否已经爬取过（如果启用了断点续爬）
            if checkpoint_id and self.checkpoint_manager:
                if await self.checkpoint_manager.check_note_is_crawled_in_checkpoint(
                    checkpoint_id=checkpoint_id, note_id=aweme_id
                ):
                    utils.logger.info(
                        f"[AwemeProcessor.batch_get_aweme_list_from_ids] Aweme {aweme_id} is already crawled, skip"
                    )
                    processed_aweme_ids.append(aweme_id)
                    continue

                # 添加到检查点
                await self.checkpoint_manager.add_note_to_checkpoint(
                    checkpoint_id=checkpoint_id,
                    note_id=aweme_id,
                    extra_params_info={},
                )

            # 创建异步任务
            task = self.get_aweme_detail_async_task(
                aweme_id=aweme_id,
                checkpoint_id=checkpoint_id,
            )
            task_list.append(task)

        # 并发执行所有任务
        aweme_details = await asyncio.gather(*task_list)
        
        # 收集成功处理的视频ID
        for aweme in aweme_details:
            if aweme:
                processed_aweme_ids.append(aweme.aweme_id)

        return processed_aweme_ids

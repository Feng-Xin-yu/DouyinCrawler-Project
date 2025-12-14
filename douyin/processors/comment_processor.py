# -*- coding: utf-8 -*-
"""
评论数据处理器
负责处理评论数据的获取、存储等操作
"""

import asyncio
from asyncio import Task
from typing import List, TYPE_CHECKING

import config
from config.base_config import PER_NOTE_MAX_COMMENTS_COUNT
from model.m_douyin import DouyinAwemeComment
from pkg.tools import utils
from repo.platform_save_data import douyin as douyin_store
from ..exception import DataFetchError

if TYPE_CHECKING:
    from ..client import DouYinApiClient
    # from repo.checkpoint.checkpoint_store import CheckpointRepoManager


class CommentProcessor:
    """
    评论数据处理器
    负责处理评论数据的获取、存储等操作
    
    主要功能：
    1. 获取视频的评论列表
    2. 获取评论的回复（二级评论）
    3. 批量处理多个视频的评论
    4. 与断点管理器交互，支持断点续爬
    """
    
    def __init__(
        self,
        dy_client: "DouYinApiClient",
        crawler_comment_semaphore: asyncio.Semaphore,
        checkpoint_manager=None,
    ):
        """
        初始化评论处理器
        
        Args:
            dy_client: 抖音API客户端
            checkpoint_manager: 断点管理器（用于断点续爬）
            crawler_comment_semaphore: 信号量，用于控制并发数量
        """
        self.dy_client = dy_client
        self.checkpoint_manager = checkpoint_manager
        self.crawler_comment_semaphore = crawler_comment_semaphore

    async def batch_get_aweme_comments(
        self,
        aweme_list: List[str],
        checkpoint_id: str = "",
    ):
        """
        批量获取视频的评论
        并发处理多个视频的评论爬取
        
        Args:
            aweme_list: 视频ID列表
            checkpoint_id: 检查点ID（用于断点续爬）
        """
        # 如果未启用评论爬取，直接返回
        if not config.ENABLE_GET_COMMENTS:
            utils.logger.info(
                f"[CommentProcessor.batch_get_aweme_comments] Crawling comment mode is not enabled"
            )
            return

        utils.logger.info(f"批量获取评论: {len(aweme_list)} 个视频")
        
        task_list: List[Task] = []
        for aweme_id in aweme_list:
            if not aweme_id:
                continue

            # 检查是否已经爬取过评论（如果启用了断点续爬）
            if checkpoint_id and self.checkpoint_manager:
                if await self.checkpoint_manager.check_note_comments_is_crawled_in_checkpoint(
                    checkpoint_id=checkpoint_id, note_id=aweme_id
                ):
                    utils.logger.debug(f"跳过已爬取评论的视频: {aweme_id}")
                    continue

            # 创建异步任务
            task = asyncio.create_task(
                self.get_comments_async_task(
                    aweme_id,
                    checkpoint_id=checkpoint_id,
                ),
                name=aweme_id,
            )
            task_list.append(task)

        # 等待所有任务完成
        if len(task_list) > 0:
            await asyncio.wait(task_list)

    async def get_comments_async_task(
        self,
        aweme_id: str,
        checkpoint_id: str = "",
    ):
        """
        异步获取视频的评论
        这是评论处理的核心方法
        
        Args:
            aweme_id: 视频ID
            checkpoint_id: 检查点ID（用于断点续爬）
        """
        async with self.crawler_comment_semaphore:
            try:
                utils.logger.debug(f"开始获取评论: {aweme_id}")
                # 获取视频的所有评论
                await self.get_aweme_all_comments(
                    aweme_id=aweme_id,
                    checkpoint_id=checkpoint_id
                )
                utils.logger.info(
                    f"[CommentProcessor.get_comments_async_task] aweme_id: {aweme_id} comments have all been obtained and filtered ..."
                )
            except DataFetchError as e:
                utils.logger.error(
                    f"[CommentProcessor.get_comments_async_task] aweme_id: {aweme_id} get comments failed, error: {e}"
                )

    async def get_aweme_all_comments(
        self,
        aweme_id: str,
        checkpoint_id: str = ""
    ):
        """
        获取视频的所有评论（包括分页）
        
        Args:
            aweme_id: 视频ID
            checkpoint_id: 检查点ID（用于断点续爬）
            
        Returns:
            List[DouyinAwemeComment]: 评论列表
        """
        result = []
        comments_has_more = 1
        comments_cursor = 0

        # 从checkpoint中获取上次保存的评论游标（如果启用了断点续爬）
        if checkpoint_id and self.checkpoint_manager:
            latest_comment_cursor = await self.checkpoint_manager.get_note_comment_cursor(
                checkpoint_id=checkpoint_id, note_id=aweme_id
            )
            if latest_comment_cursor:
                try:
                    comments_cursor = int(latest_comment_cursor)
                    utils.logger.debug(f"从断点继续: cursor={comments_cursor}")
                except (ValueError, TypeError):
                    utils.logger.warning(
                        f"[CommentProcessor.get_aweme_all_comments] Invalid cursor format: {latest_comment_cursor}, starting from beginning"
                    )
                    comments_cursor = 0

        # 循环获取所有评论（分页）
        while comments_has_more:
            # 获取一页评论
            comments, comments_res = await self.dy_client.get_aweme_comments(
                aweme_id, comments_cursor
            )
            comments_has_more = comments_res.get("has_more", 0)
            comments_cursor = comments_res.get("cursor", 0)

            # 更新评论游标到checkpoint中（如果启用了断点续爬）
            if checkpoint_id and self.checkpoint_manager and comments_cursor is not None:
                await self.checkpoint_manager.update_note_comment_cursor(
                    checkpoint_id=checkpoint_id,
                    note_id=aweme_id,
                    comment_cursor=str(comments_cursor),
                )

            if not comments:
                continue
            
            result.extend(comments)
            
            # 保存评论到数据库
            await douyin_store.batch_update_dy_aweme_comments(aweme_id, comments)
            
            # 检查是否超过最大评论数量限制
            if (
                PER_NOTE_MAX_COMMENTS_COUNT
                and len(result) >= PER_NOTE_MAX_COMMENTS_COUNT
            ):
                utils.logger.info(
                    f"[CommentProcessor.get_aweme_all_comments] The number of comments exceeds the limit: {PER_NOTE_MAX_COMMENTS_COUNT}"
                )
                break
            
            # 爬虫请求间隔时间
            await asyncio.sleep(config.CRAWLER_TIME_SLEEP)
            
            # 获取二级评论（如果启用了）
            sub_comments = await self.get_comments_all_sub_comments(
                aweme_id, comments
            )
            result.extend(sub_comments)

        # 标记该视频的评论已完全爬取（如果启用了断点续爬）
        if checkpoint_id and self.checkpoint_manager:
            await self.checkpoint_manager.update_note_comment_cursor(
                checkpoint_id=checkpoint_id,
                note_id=aweme_id,
                comment_cursor=str(comments_cursor),
                is_success_crawled_comments=True,
            )

        return result

    async def get_comments_all_sub_comments(
        self,
        aweme_id: str,
        comments: List[DouyinAwemeComment]
    ) -> List[DouyinAwemeComment]:
        """
        获取指定一级评论下的所有二级评论（回复）
        该方法会查找一级评论下的所有二级评论信息
        
        Args:
            aweme_id: 视频ID
            comments: 一级评论列表
            
        Returns:
            List[DouyinAwemeComment]: 二级评论列表
        """
        # 如果未启用二级评论爬取，直接返回
        if not config.ENABLE_GET_SUB_COMMENTS:
            utils.logger.info(
                f"[CommentProcessor.get_comments_all_sub_comments] Crawling sub_comment mode is not enabled"
            )
            return []
        
        result = []
        for comment in comments:
            # 检查是否有回复
            reply_comment_total = int(comment.sub_comment_count) if comment.sub_comment_count else 0
            if reply_comment_total > 0:
                comment_id = comment.comment_id
                sub_comments_has_more = 1
                sub_comments_cursor = 0
                
                # 循环获取所有二级评论（分页）
                while sub_comments_has_more:
                    sub_comments, sub_comments_res = await self.dy_client.get_sub_comments(
                        comment_id, sub_comments_cursor, aweme_id
                    )
                    sub_comments_has_more = sub_comments_res.get("has_more", 0)
                    sub_comments_cursor = sub_comments_res.get("cursor", 0)
                    
                    if not sub_comments:
                        continue
                    
                    result.extend(sub_comments)
                    
                    # 保存子评论到数据库
                    await douyin_store.batch_update_dy_aweme_comments(aweme_id, sub_comments)

                    # 爬虫请求间隔时间
                    await asyncio.sleep(config.CRAWLER_TIME_SLEEP)
        
        return result

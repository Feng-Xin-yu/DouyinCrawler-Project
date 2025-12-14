# -*- coding: utf-8 -*-
"""
创作者处理器
处理指定创作者主页的爬取任务
"""

import asyncio
from typing import Dict, List, TYPE_CHECKING

import config
import constant
from model.m_checkpoint import Checkpoint
from pkg.tools import utils
from repo.platform_save_data import douyin as douyin_store
from ..extractor import DouyinExtractor
from .base_handler import BaseHandler

if TYPE_CHECKING:
    from ..client import DouYinApiClient
    # from repo.checkpoint.checkpoint_store import CheckpointRepoManager
    from ..processors.aweme_processor import AwemeProcessor
    from ..processors.comment_processor import CommentProcessor


class CreatorHandler(BaseHandler):
    """
    创作者处理器
    处理指定创作者主页的爬取任务
    
    主要功能：
    1. 获取创作者信息
    2. 获取创作者的所有视频
    3. 获取视频评论
    """
    
    def __init__(
        self,
        dy_client: "DouYinApiClient",
        checkpoint_manager=None,
        aweme_processor=None,
        comment_processor=None,
    ):
        """
        初始化创作者处理器
        
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
        处理创作者爬取任务
        
        Returns:
            None
        """
        await self.get_creators_and_videos()

    @staticmethod
    def _find_creator_index_in_creator_list(creator_id: str) -> int:
        """
        在创作者列表中找到指定创作者的索引
        
        Args:
            creator_id: 创作者ID
            
        Returns:
            int: 创作者在列表中的索引，如果未找到返回-1
        """
        creator_list = config.DY_CREATOR_ID_LIST
        for index, creator_item in enumerate(creator_list):
            if creator_item == creator_id:
                return index
        return -1

    async def get_creators_and_videos(self) -> None:
        """
        获取指定创作者的信息和视频
        
        Returns:
            None
        """
        utils.logger.info(
            "[CreatorHandler.get_creators_and_videos] Begin get douyin creators"
        )
        
        checkpoint = Checkpoint(platform=constant.DOUYIN_PLATFORM_NAME, mode=constant.CRALER_TYPE_CREATOR)
        creator_list = config.DY_CREATOR_ID_LIST
        if not creator_list:
            utils.logger.error(
                "[CreatorHandler.get_creators_and_videos] DY_CREATOR_ID_LIST is empty, please configure it"
            )
            return

        # 断点续爬
        from pkg.tools.output_formatter import OutputFormatter
        
        if config.ENABLE_CHECKPOINT and self.checkpoint_manager:
            lastest_checkpoint = await self.checkpoint_manager.load_checkpoint(
                platform=constant.DOUYIN_PLATFORM_NAME,
                mode=constant.CRALER_TYPE_CREATOR,
                checkpoint_id=config.SPECIFIED_CHECKPOINT_ID,
            )
            if lastest_checkpoint:
                checkpoint = lastest_checkpoint
                # 显示断点续爬信息
                checkpoint_dict = checkpoint.model_dump()
                OutputFormatter.print_resume_info(checkpoint_dict)
                
                # 找到当前创作者在列表中的位置，从该位置继续处理
                creator_index = self._find_creator_index_in_creator_list(
                    lastest_checkpoint.current_creator_id
                )
                if creator_index == -1:
                    utils.logger.error(
                        f"[CreatorHandler.get_creators_and_videos] Creator {lastest_checkpoint.current_creator_id} not found in creator list"
                    )
                    creator_index = 0
                # 从断点的创作者位置继续处理
                creator_list = creator_list[creator_index:]
            else:
                checkpoint = await self.checkpoint_manager.save_checkpoint(checkpoint)
                OutputFormatter.print_info("创建新断点")

        total_creators = len(creator_list)
        OutputFormatter.print_section(f"开始爬取创作者 (共 {total_creators} 个)")

        for idx, user_id in enumerate(creator_list, 1):
            # 更新当前创作者ID到检查点
            if config.ENABLE_CHECKPOINT and self.checkpoint_manager:
                checkpoint.current_creator_id = user_id
                await self.checkpoint_manager.save_checkpoint(checkpoint)
            
            OutputFormatter.print_info(f"处理创作者 {idx}/{total_creators}: {user_id[:20]}...")
            
            # 获取创作者信息
            creator = await self.dy_client.get_user_info(user_id)
            if creator:
                await douyin_store.save_creator(user_id, creator=creator)
                OutputFormatter.print_success(f"创作者信息已保存: {creator.nickname or user_id}")

            # 获取创作者的所有视频
            await self.get_all_user_aweme_posts(
                sec_user_id=user_id, checkpoint_id=checkpoint.id if config.ENABLE_CHECKPOINT else ""
            )

    async def get_all_user_aweme_posts(self, sec_user_id: str, checkpoint_id: str = ""):
        """
        获取指定用户的所有视频
        
        Args:
            sec_user_id: 用户ID（sec_uid）
            
        Returns:
            List: 视频列表
        """
        posts_has_more = 1
        max_cursor = "0"
        if checkpoint_id and self.checkpoint_manager:
            cp = await self.checkpoint_manager.load_checkpoint_by_id(checkpoint_id)
            if cp and cp.current_creator_page:
                max_cursor = cp.current_creator_page
        result = []
        extractor = DouyinExtractor()
        
        from pkg.tools.output_formatter import OutputFormatter
        
        while posts_has_more == 1 and len(result) < config.CRAWLER_MAX_NOTES_COUNT:
            try:
                # 调用API获取用户视频列表
                aweme_post_res = await self.dy_client.get_user_aweme_posts(
                    sec_user_id, max_cursor
                )
                
                posts_has_more = aweme_post_res.get("has_more", 0)
                max_cursor = aweme_post_res.get("max_cursor", "0")
                aweme_list = aweme_post_res.get("aweme_list", [])
                
                if not aweme_list:
                    OutputFormatter.print_info("该创作者没有更多视频")
                    break

                OutputFormatter.print_progress(
                    len(result) + len(aweme_list),
                    config.CRAWLER_MAX_NOTES_COUNT,
                    "视频",
                    "已获取",
                    show_percentage=True
                )

                aweme_ids = []
                saved_count = 0
                skipped_count = 0
                
                for aweme_info in aweme_list:
                    aweme_id = aweme_info.get("aweme_id", "")
                    if not aweme_id:
                        continue

                    aweme_ids.append(aweme_id)

                    # 检查是否已经爬取过（断点续爬）
                    if checkpoint_id and self.checkpoint_manager:
                        if await self.checkpoint_manager.check_note_is_crawled_in_checkpoint(
                                checkpoint_id=checkpoint_id, note_id=aweme_id
                        ):
                            skipped_count += 1
                            continue
                        await self.checkpoint_manager.add_note_to_checkpoint(
                            checkpoint_id=checkpoint_id,
                            note_id=aweme_id,
                            extra_params_info={},
                            is_success_crawled=True,
                        )

                    # 提取并保存视频数据
                    aweme = extractor.extract_aweme_from_dict(aweme_info)
                    if aweme:
                        await douyin_store.update_douyin_aweme(aweme_item=aweme)
                        saved_count += 1
                        # 只显示视频ID，不显示标题（避免输出过多）
                        if saved_count <= 3 or saved_count % 10 == 0:  # 只显示前3个和每10个
                            OutputFormatter.print_video_info(aweme_id, action="已保存")

                if skipped_count > 0:
                    OutputFormatter.print_info(f"跳过已爬取视频: {skipped_count} 个")

                # 处理评论
                if config.ENABLE_GET_COMMENTS and aweme_ids:
                    OutputFormatter.print_info(f"开始爬取评论 (视频数: {len(aweme_ids)})")
                
                await self.comment_processor.batch_get_aweme_comments(
                    aweme_ids, checkpoint_id=checkpoint_id
                )
                
                result.extend(aweme_list)

                # 爬虫请求间隔时间
                await asyncio.sleep(config.CRAWLER_TIME_SLEEP)

            except KeyboardInterrupt:
                # 用户中断
                from pkg.tools.output_formatter import OutputFormatter
                
                checkpoint_data = None
                if checkpoint_id and self.checkpoint_manager:
                    cp = await self.checkpoint_manager.load_checkpoint_by_id(checkpoint_id)
                    if cp:
                        checkpoint_data = cp.model_dump()
                
                OutputFormatter.print_interrupt_info(
                    reason="用户中断 (Ctrl+C)",
                    checkpoint_data=checkpoint_data,
                    stats={
                        "已获取视频数": len(result),
                        "当前页码": max_cursor,
                        "创作者ID": sec_user_id[:20] + "..."
                    }
                )
                raise

            except Exception as ex:
                # 其他异常
                checkpoint_data = None
                if checkpoint_id and self.checkpoint_manager:
                    cp = await self.checkpoint_manager.load_checkpoint_by_id(checkpoint_id)
                    if cp:
                        checkpoint_data = cp.model_dump()
                
                OutputFormatter.print_interrupt_info(
                    reason=f"发生异常: {str(ex)[:100]}",
                    checkpoint_data=checkpoint_data,
                    stats={
                        "已获取视频数": len(result),
                        "当前页码": max_cursor,
                        "创作者ID": sec_user_id[:20] + "..."
                    }
                )
                
                utils.log_error_with_context(
                    utils.logger,
                    ex,
                    context={
                        "用户ID": sec_user_id,
                        "当前页码": max_cursor,
                        "已获取视频数": len(result),
                        "检查点ID": checkpoint_id if checkpoint_id else "未启用",
                    }
                )
                utils.logger.opt(exception=True).error("完整异常堆栈:")
                break

            # 更新checkpoint cursor
            if checkpoint_id and self.checkpoint_manager:
                cp = await self.checkpoint_manager.load_checkpoint_by_id(checkpoint_id)
                if cp:
                    cp.current_creator_page = str(max_cursor)
                    cp.current_creator_id = sec_user_id
                    await self.checkpoint_manager.update_checkpoint(cp)

        OutputFormatter.print_success(f"创作者视频爬取完成: 共 {len(result)} 个视频")
        return result

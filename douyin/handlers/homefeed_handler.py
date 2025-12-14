# -*- coding: utf-8 -*-
"""
首页推荐处理器
处理首页推荐视频的爬取任务
"""

import asyncio
import json
from typing import Dict, List, TYPE_CHECKING

import config
import constant
from model.m_checkpoint import Checkpoint
from pkg.tools import utils
from repo.platform_save_data import douyin as douyin_store
from ..extractor import DouyinExtractor
from ..field import HomeFeedTagIdType
from .base_handler import BaseHandler

if TYPE_CHECKING:
    from ..client import DouYinApiClient
    # from repo.checkpoint.checkpoint_store import CheckpointRepoManager
    from ..processors.aweme_processor import AwemeProcessor
    from ..processors.comment_processor import CommentProcessor


class HomefeedHandler(BaseHandler):
    """
    首页推荐处理器
    处理首页推荐视频的爬取任务
    
    主要功能：
    1. 获取首页推荐视频列表
    2. 保存视频数据
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
        初始化首页推荐处理器
        
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
        处理首页推荐爬取任务
        
        Returns:
            None
        """
        await self.get_homefeed_awemes()

    async def get_homefeed_awemes(self):
        """
        获取首页推荐视频和评论
        
        Returns:
            None
        """
        utils.logger.info(
            "[HomefeedHandler.get_homefeed_awemes] Begin get douyin homefeed awemes"
        )

        # 断点续爬
        checkpoint = Checkpoint(
            platform=constant.DOUYIN_PLATFORM_NAME,
            mode=constant.CRALER_TYPE_HOMEFEED,
            current_homefeed_cursor="",
            current_homefeed_note_index=0,
        )
        if config.ENABLE_CHECKPOINT and self.checkpoint_manager:
            lastest_checkpoint = await self.checkpoint_manager.load_checkpoint(
                platform=constant.DOUYIN_PLATFORM_NAME,
                mode=constant.CRALER_TYPE_HOMEFEED,
                checkpoint_id=config.SPECIFIED_CHECKPOINT_ID,
            )
            if lastest_checkpoint:
                checkpoint = lastest_checkpoint
                utils.logger.info(
                    f"[HomefeedHandler.get_homefeed_awemes] Load last checkpoint: {lastest_checkpoint.id}"
                )
            else:
                checkpoint = await self.checkpoint_manager.save_checkpoint(checkpoint)

        current_refresh_index = checkpoint.current_homefeed_note_index or 0
        per_page_count = 20
        saved_aweme_count = 0
        extractor = DouyinExtractor()
        
        while saved_aweme_count < config.CRAWLER_MAX_NOTES_COUNT:
            try:
                utils.logger.info(
                    f"[HomefeedHandler.get_homefeed_awemes] Get homefeed awemes, "
                    f"current_refresh_index: {current_refresh_index}, per_page_count: {per_page_count}"
                )

                # 调用API获取首页推荐视频
                homefeed_aweme_res = await self.dy_client.get_homefeed_aweme_list(
                    tag_id=HomeFeedTagIdType.ALL,
                    refresh_index=current_refresh_index,
                    count=per_page_count,
                )
                
                if not homefeed_aweme_res or homefeed_aweme_res.get("StatusCode") != 0:
                    utils.logger.info(
                        f"[HomefeedHandler.get_homefeed_awemes] No more content!"
                    )
                    break

                # 提取视频列表
                aweme_ids = []
                cards: List[Dict] = homefeed_aweme_res.get("cards", [])
                # 只处理type=1的卡片（视频卡片）
                filtered_cards = [card for card in cards if card.get("type") == 1]

                for card in filtered_cards:
                    # 限制爬取数量
                    if saved_aweme_count >= config.CRAWLER_MAX_NOTES_COUNT:
                        utils.logger.info(
                            f"[HomefeedHandler.get_homefeed_awemes] Reached max awemes count: {config.CRAWLER_MAX_NOTES_COUNT}"
                        )
                        break

                    aweme_json_str: str = card.get("aweme", "")
                    if not aweme_json_str:
                        continue

                    try:
                        aweme_info: Dict = json.loads(aweme_json_str)
                    except json.JSONDecodeError:
                        utils.logger.warning(
                            f"[HomefeedHandler.get_homefeed_awemes] Failed to parse aweme JSON"
                        )
                        continue

                    aweme_id = aweme_info.get("aweme_id", "")
                    if not aweme_id:
                        continue

                    aweme_ids.append(aweme_id)

                    # 检查是否已经爬取过（断点续爬）
                    if checkpoint.id and self.checkpoint_manager and config.ENABLE_CHECKPOINT:
                        if await self.checkpoint_manager.check_note_is_crawled_in_checkpoint(
                                checkpoint_id=checkpoint.id, note_id=aweme_id
                        ):
                            saved_aweme_count += 1
                            continue
                        await self.checkpoint_manager.add_note_to_checkpoint(
                            checkpoint_id=checkpoint.id,
                            note_id=aweme_id,
                            extra_params_info={},
                            is_success_crawled=True,
                        )

                    # 提取并保存视频数据
                    aweme = extractor.extract_aweme_from_dict(aweme_info)
                    if aweme:
                        await douyin_store.update_douyin_aweme(aweme_item=aweme)
                        saved_aweme_count += 1

                # 处理评论
                await self.comment_processor.batch_get_aweme_comments(
                    aweme_ids, checkpoint_id=checkpoint.id if config.ENABLE_CHECKPOINT else ""
                )
                
                current_refresh_index += per_page_count

                # 爬虫请求间隔时间
                await asyncio.sleep(config.CRAWLER_TIME_SLEEP)

            except Exception as ex:
                utils.logger.error(
                    f"[HomefeedHandler.get_homefeed_awemes] Get homefeed awemes error: {ex}",
                    exc_info=True
                )
                # 发生异常时，记录当前爬取的索引
                utils.logger.info(
                    "------------------------------------------记录当前爬取的索引------------------------------------------"
                )
                for i in range(3):
                    utils.logger.error(
                        f"[HomefeedHandler.get_homefeed_awemes] Current refresh_index: {current_refresh_index}"
                    )
                utils.logger.info(
                    "------------------------------------------记录当前爬取的索引---------------------------------------------------"
                )
                return

            # 更新检查点
            finally:
                if config.ENABLE_CHECKPOINT and self.checkpoint_manager and checkpoint.id:
                    checkpoint.current_homefeed_note_index = current_refresh_index
                    await self.checkpoint_manager.update_checkpoint(checkpoint)

        utils.logger.info(
            "[HomefeedHandler.get_homefeed_awemes] Douyin homefeed awemes crawler finished ..."
        )

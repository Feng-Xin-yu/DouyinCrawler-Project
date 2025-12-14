# -*- coding: utf-8 -*-
"""
搜索处理器
处理关键词搜索爬取任务
"""

import asyncio
from typing import Dict, List, TYPE_CHECKING

import config
import constant
from model.m_checkpoint import Checkpoint
from pkg.tools import utils
from repo.platform_save_data import douyin as douyin_store
from var import source_keyword_var
from ..extractor import DouyinExtractor
from ..field import PublishTimeType
from .base_handler import BaseHandler

if TYPE_CHECKING:
    from ..client import DouYinApiClient
    # from repo.checkpoint.checkpoint_store import CheckpointRepoManager
    from ..processors.aweme_processor import AwemeProcessor
    from ..processors.comment_processor import CommentProcessor


class SearchHandler(BaseHandler):
    """
    搜索处理器
    处理关键词搜索爬取任务
    
    主要功能：
    1. 解析关键词列表
    2. 循环调用搜索API
    3. 提取视频列表
    4. 保存视频数据
    5. 处理视频评论
    6. 处理分页
    """
    
    def __init__(
        self,
        dy_client: "DouYinApiClient",
        checkpoint_manager=None,
        aweme_processor=None,
        comment_processor=None,
    ):
        """
        初始化搜索处理器
        
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
        处理搜索爬取任务
        
        Returns:
            None
        """
        await self.search()

    @staticmethod
    def _get_search_keyword_list() -> List[str]:
        """
        获取搜索关键词列表
        
        Returns:
            List[str]: 关键词列表
        """
        if not config.KEYWORDS:
            utils.logger.error("[SearchHandler._get_search_keyword_list] 关键词为空，请配置KEYWORDS")
            return []
        return [keyword.strip() for keyword in config.KEYWORDS.split(",") if keyword.strip()]

    async def search(self) -> None:
        """
        执行搜索爬取
        搜索视频列表并获取评论信息
        
        Returns:
            None
        """
        utils.logger.info("[SearchHandler.search] Begin search douyin keywords")
        
        # 抖音每页固定返回20条
        dy_limit_count = 20
        if config.CRAWLER_MAX_NOTES_COUNT < dy_limit_count:
            config.CRAWLER_MAX_NOTES_COUNT = dy_limit_count

        from pkg.tools.output_formatter import OutputFormatter
        
        keyword_list = self._get_search_keyword_list()
        if not keyword_list:
            OutputFormatter.print_error("关键词列表为空，退出")
            return

        # 断点续爬
        checkpoint = Checkpoint(
            platform=constant.DOUYIN_PLATFORM_NAME,
            mode=constant.CRALER_TYPE_SEARCH,
            current_search_page=1,
        )
        if config.ENABLE_CHECKPOINT and self.checkpoint_manager:
            lastest_checkpoint = await self.checkpoint_manager.load_checkpoint(
                platform=constant.DOUYIN_PLATFORM_NAME,
                mode=constant.CRALER_TYPE_SEARCH,
                checkpoint_id=config.SPECIFIED_CHECKPOINT_ID,
            )
            if lastest_checkpoint:
                checkpoint = lastest_checkpoint
                checkpoint_dict = checkpoint.model_dump()
                OutputFormatter.print_resume_info(checkpoint_dict)
            else:
                checkpoint = await self.checkpoint_manager.save_checkpoint(checkpoint)
                OutputFormatter.print_info("创建新断点")

        total_keywords = len(keyword_list)
        OutputFormatter.print_section(f"开始搜索爬取 (关键词数: {total_keywords})")

        for idx, keyword in enumerate(keyword_list, 1):
            # 设置来源关键词到上下文变量
            source_keyword_var.set(keyword)

            # 持续使用 checkpoint 中保存的页码/id
            page = checkpoint.current_search_page if checkpoint.current_search_keyword == keyword else 1
            dy_search_id = checkpoint.current_search_id if checkpoint.current_search_keyword == keyword else ""
            saved_aweme_count = (page - 1) * dy_limit_count
            
            OutputFormatter.print_info(f"搜索关键词 {idx}/{total_keywords}: {keyword}")

            while saved_aweme_count < config.CRAWLER_MAX_NOTES_COUNT:
                try:
                    OutputFormatter.print_progress(
                        saved_aweme_count,
                        config.CRAWLER_MAX_NOTES_COUNT,
                        "视频",
                        f"关键词: {keyword} | 页码: {page}",
                        show_percentage=True
                    )
                    
                    # 调用搜索API
                    posts_res = await self.dy_client.search_info_by_keyword(
                        keyword=keyword,
                        offset=(page - 1) * dy_limit_count,
                        publish_time=PublishTimeType(config.PUBLISH_TIME_TYPE),
                        search_id=dy_search_id,
                    )

                    if "data" not in posts_res:
                        OutputFormatter.print_error(f"搜索失败，账号可能被风控: {keyword}")
                        break

                    # 获取search_id用于下一页
                    dy_search_id = posts_res.get("extra", {}).get("logid", "")
                    aweme_id_list: List[str] = []

                    post_item_list: List[Dict] = posts_res.get("data", [])
                    if len(post_item_list) == 0:
                        OutputFormatter.print_warning(f"关键词 {keyword} 没有更多结果")
                        break

                    # 提取视频信息
                    extractor = DouyinExtractor()
                    saved_count = 0
                    skipped_count = 0
                    
                    for post_item in post_item_list:
                        try:
                            # 提取aweme_info
                            aweme_info: Dict = (
                                post_item.get("aweme_info")
                                or post_item.get("aweme_mix_info", {}).get("mix_items", [{}])[0]
                            )
                        except (TypeError, IndexError):
                            continue

                        aweme_id = aweme_info.get("aweme_id", "")
                        if not aweme_id:
                            continue

                        aweme_id_list.append(aweme_id)

                        # 检查是否已经爬取过（断点续爬）
                        if config.ENABLE_CHECKPOINT and self.checkpoint_manager and checkpoint.id:
                            if await self.checkpoint_manager.check_note_is_crawled_in_checkpoint(
                                checkpoint_id=checkpoint.id, note_id=aweme_id
                            ):
                                skipped_count += 1
                                saved_aweme_count += 1
                                continue

                        # 提取并保存视频数据
                        aweme = extractor.extract_aweme_from_dict(aweme_info)
                        if aweme:
                            await douyin_store.update_douyin_aweme(aweme_item=aweme)
                            saved_count += 1
                            saved_aweme_count += 1
                            # 只显示部分视频ID（避免输出过多）
                            if saved_count <= 3 or saved_count % 10 == 0:
                                OutputFormatter.print_video_info(aweme_id, action="已保存")

                    if skipped_count > 0:
                        OutputFormatter.print_info(f"跳过已爬取视频: {skipped_count} 个")
                    
                    # 处理评论
                    if config.ENABLE_GET_COMMENTS and aweme_id_list:
                        OutputFormatter.print_info(f"开始爬取评论 (视频数: {len(aweme_id_list)})")
                    
                    await self.comment_processor.batch_get_aweme_comments(
                        aweme_id_list, checkpoint_id=checkpoint.id
                    )

                    page += 1

                    # 爬虫请求间隔时间
                    await asyncio.sleep(config.CRAWLER_TIME_SLEEP)

                except KeyboardInterrupt:
                    # 用户中断
                    checkpoint_data = None
                    if checkpoint.id:
                        cp = await self.checkpoint_manager.load_checkpoint_by_id(checkpoint.id)
                        if cp:
                            checkpoint_data = cp.model_dump()
                    
                    OutputFormatter.print_interrupt_info(
                        reason="用户中断 (Ctrl+C)",
                        checkpoint_data=checkpoint_data,
                        stats={
                            "已爬取视频数": saved_aweme_count,
                            "当前关键词": keyword,
                            "当前页码": page,
                        }
                    )
                    raise

                except Exception as ex:
                    # 其他异常
                    checkpoint_data = None
                    if checkpoint.id:
                        cp = await self.checkpoint_manager.load_checkpoint_by_id(checkpoint.id)
                        if cp:
                            checkpoint_data = cp.model_dump()
                    
                    OutputFormatter.print_interrupt_info(
                        reason=f"发生异常: {str(ex)[:100]}",
                        checkpoint_data=checkpoint_data,
                        stats={
                            "已爬取视频数": saved_aweme_count,
                            "当前关键词": keyword,
                            "当前页码": page,
                        }
                    )
                    
                    utils.log_error_with_context(
                        utils.logger,
                        ex,
                        context={
                            "搜索关键词": keyword,
                            "当前页码": page,
                            "搜索ID": dy_search_id if 'dy_search_id' in locals() else "未知",
                            "检查点ID": checkpoint.id if checkpoint and hasattr(checkpoint, 'id') else "未启用",
                        }
                    )
                    utils.logger.opt(exception=True).error("完整异常堆栈:")
                    return

                # 更新检查点
                finally:
                    if config.ENABLE_CHECKPOINT and self.checkpoint_manager and checkpoint.id:
                        checkpoint.current_search_keyword = keyword
                        checkpoint.current_search_page = page
                        checkpoint.current_search_id = dy_search_id
                        await self.checkpoint_manager.update_checkpoint(checkpoint)

        OutputFormatter.print_success(f"关键词搜索完成: 共爬取 {saved_aweme_count} 个视频")

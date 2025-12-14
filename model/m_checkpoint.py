# -*- coding: utf-8 -*-
"""
断点续爬数据模型
用于在爬虫过程中保存当前位置，支持任务恢复
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CheckpointNote(BaseModel):
    """
    检查点中的帖子信息
    """
    note_id: str = Field(..., description="帖子ID")
    extra_params_info: Optional[Dict[str, Any]] = Field(
        None, description="额外参数信息"
    )
    is_success_crawled: bool = Field(False, description="是否成功爬取")
    is_success_crawled_comments: bool = Field(False, description="是否成功爬取评论")
    current_note_comment_cursor: Optional[str] = Field(
        "", description="当前帖子评论游标"
    )


class Checkpoint(BaseModel):
    """
    检查点
    用于保存爬虫的当前状态，支持任务恢复
    """

    # 主键
    id: Optional[str] = Field(None, description="检查点ID")

    # 基础字段
    platform: str = Field(
        ..., description="平台名称，如 douyin"
    )
    mode: str = Field(..., description="模式：search/detail/creator/homefeed")

    # 搜索模式相关字段
    current_search_keyword: Optional[str] = Field(None, description="当前搜索关键词")
    current_search_page: Optional[int] = Field(None, description="当前搜索页码")
    current_search_id: Optional[str] = Field(None, description="当前搜索ID")

    # 创作者模式相关字段
    current_creator_id: Optional[str] = Field(None, description="当前创作者ID")
    current_creator_page: Optional[str] = Field(None, description="当前创作者页码")

    # 首页推荐流相关字段
    current_homefeed_cursor: Optional[str] = Field(
        None, description="当前首页推荐流游标"
    )
    current_homefeed_note_index: Optional[int] = Field(
        None, description="当前首页推荐流笔记索引"
    )

    # 帖子相关字段（搜索模式、详情模式、创作者模式、首页推荐流能用到）
    crawled_note_list: Optional[List[CheckpointNote]] = Field(
        [], description="已爬取的帖子列表"
    )

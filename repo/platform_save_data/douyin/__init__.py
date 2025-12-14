# -*- coding: utf-8 -*-
"""
抖音数据存储模块
提供抖音视频、评论、创作者数据的存储功能
"""

from typing import List

import config
from base.base_crawler import AbstractStore
from model.m_douyin import DouyinAweme, DouyinAwemeComment, DouyinCreator
from pkg.tools import utils
from var import source_keyword_var

from .douyin_store_impl import (
    DouyinCsvStoreImplement,
    DouyinJsonStoreImplement,
)


class DouyinStoreFactory:
    """
    抖音存储工厂类
    根据配置创建不同类型的存储实例（CSV/JSON）
    """
    STORES = {
        "csv": DouyinCsvStoreImplement,
        "json": DouyinJsonStoreImplement,
    }

    @staticmethod
    def create_store() -> AbstractStore:
        """
        创建存储实例
        
        Returns:
            AbstractStore: 存储实例
            
        Raises:
            ValueError: 如果存储类型无效
        """
        store_class = DouyinStoreFactory.STORES.get(config.SAVE_DATA_OPTION)
        if not store_class:
            raise ValueError(
                "[DouyinStoreFactory.create_store] Invalid save option only supported csv or json ..."
            )
        return store_class()


async def batch_update_douyin_awemes(awemes: List[DouyinAweme]):
    """
    批量更新抖音视频
    
    Args:
        awemes: 视频列表
    """
    if not awemes:
        return

    for aweme_item in awemes:
        await update_douyin_aweme(aweme_item)


async def update_douyin_aweme(aweme_item: DouyinAweme):
    """
    更新抖音视频
    将视频数据保存到存储层（CSV/JSON）
    
    Args:
        aweme_item: 视频对象
    """
    # 设置来源关键词
    aweme_item.source_keyword = source_keyword_var.get()
    
    # 转换为字典并添加时间戳
    local_db_item = aweme_item.model_dump()
    local_db_item.update({"last_modify_ts": utils.get_current_timestamp()})

    # 打印日志
    print_title = aweme_item.title[:30] if aweme_item.title else aweme_item.desc[:30]
    utils.logger.info(
        f"[store.douyin.update_douyin_aweme] douyin aweme, id: {aweme_item.aweme_id}, title: {print_title}"
    )
    
    # 保存到存储层
    await DouyinStoreFactory.create_store().store_content(local_db_item)


async def batch_update_dy_aweme_comments(aweme_id: str, comments: List[DouyinAwemeComment]):
    """
    批量更新抖音视频评论
    
    Args:
        aweme_id: 视频ID
        comments: 评论列表
    """
    if not comments:
        return

    for comment_item in comments:
        await update_dy_aweme_comment(comment_item)


async def update_dy_aweme_comment(comment_item: DouyinAwemeComment):
    """
    更新抖音视频评论
    将评论数据保存到存储层（CSV/JSON）
    
    Args:
        comment_item: 评论对象
    """
    # 转换为字典并添加时间戳
    local_db_item = comment_item.model_dump()
    local_db_item.update({"last_modify_ts": utils.get_current_timestamp()})

    utils.logger.info(
        f"[store.douyin.update_dy_aweme_comment] douyin aweme comment, "
        f"aweme_id: {comment_item.aweme_id}, comment_id: {comment_item.comment_id}"
    )
    
    # 保存到存储层
    await DouyinStoreFactory.create_store().store_comment(local_db_item)


async def save_creator(user_id: str, creator: DouyinCreator):
    """
    保存抖音创作者信息
    
    Args:
        user_id: 用户ID
        creator: 创作者对象
    """
    if not creator:
        return

    # 转换为字典并添加时间戳
    local_db_item = creator.model_dump()
    local_db_item.update({"last_modify_ts": utils.get_current_timestamp()})

    utils.logger.info(
        f"[store.douyin.save_creator] douyin creator, id: {creator.user_id}, nickname: {creator.nickname}"
    )
    
    # 保存到存储层
    await DouyinStoreFactory.create_store().store_creator(local_db_item)

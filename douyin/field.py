# -*- coding: utf-8 -*-
"""
抖音字段枚举定义
定义搜索类型、排序类型、发布时间类型等枚举
"""

from enum import Enum


class SearchChannelType(Enum):
    """
    搜索频道类型枚举
    """
    GENERAL = "aweme_general"  # 综合
    VIDEO = "aweme_video_web"  # 视频
    USER = "aweme_user_web"  # 用户
    LIVE = "aweme_live"  # 直播


class SearchSortType(Enum):
    """
    搜索排序类型枚举
    """
    GENERAL = 0  # 综合排序
    MOST_LIKE = 1  # 最多点赞
    LATEST = 2  # 最新发布


class PublishTimeType(Enum):
    """
    发布时间类型枚举
    """
    UNLIMITED = 0  # 不限
    ONE_DAY = 1  # 一天内
    ONE_WEEK = 7  # 一周内
    SIX_MONTH = 180  # 半年内


class HomeFeedTagIdType(Enum):
    """
    首页推荐标签类型枚举
    """
    ALL = 0  # 全部
    KNOWLEDGE = 300213  # 知识
    SPORTS = 300207  # 体育
    AUTO = 300218  # 汽车
    ANIME = 300206  # 二次元
    GAME = 300205  # 游戏
    MOVIE = 300215  # 影视
    LIFE_VLOG = 300216  # 生活vlog
    TRAVEL = 300221  # 旅行
    MINI_DRAMA = 300214  # 小剧场
    FOOD = 300204  # 美食
    AGRICULTURE = 300219  # 三农
    MUSIC = 300209  # 音乐
    ANIMAL = 300220  # 动物
    PARENTING = 300217  # 亲子
    FASHION = 300222  # 美妆穿搭

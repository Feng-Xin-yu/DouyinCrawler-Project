# -*- coding: utf-8 -*-
"""
基础配置模块
定义爬虫的基础配置项，包括爬取类型、关键词、数量控制等
"""

import os
from typing import List

from constant import EXCEL_ACCOUNT_SAVE

# ==================== 爬取基础配置 ====================
# 搜索关键词，多个关键词用逗号分隔
# 例如：KEYWORDS = "Python,爬虫,抖音"
KEYWORDS = "Python,爬虫"

# 发布时间类型（抖音专用）
# 0: 不限, 1: 一天内, 7: 一周内, 30: 一个月内
PUBLISH_TIME_TYPE = 0

# 爬取类型
# search: 关键词搜索爬取
# detail: 视频详情爬取
# creator: 创作者主页数据爬取
# homefeed: 首页推荐爬取
CRAWLER_TYPE = "creator"

# ==================== 数据存储配置 ====================
# 数据保存类型，支持两种类型：csv、json
# csv: 保存为CSV文件，易于查看和分析
# json: 保存为JSON文件，结构化数据
SAVE_DATA_OPTION = "csv"  # csv or json

# 账号池保存类型，使用Excel方式
# 账号信息存储在 config/accounts_cookies.xlsx 文件中
ACCOUNT_POOL_SAVE_TYPE = EXCEL_ACCOUNT_SAVE

# ==================== 爬取控制配置 ====================
# 爬取开始页数，默认从第一页开始
START_PAGE = 1

# 爬取视频的最大数量控制
# 设置为0表示不限制（不推荐，可能导致爬取时间过长）
CRAWLER_MAX_NOTES_COUNT = 40

# 并发爬虫数量控制
# ⚠️⚠️⚠️ 重要：请勿设置过大，避免对平台造成压力
# 建议设置为1-3，仅用于学习python并发控制技术
MAX_CONCURRENCY_NUM = 1

# ==================== 评论爬取配置 ====================
# 是否开启爬评论模式，默认开启
ENABLE_GET_COMMENTS = True

# 是否开启爬二级评论模式，默认不开启
# 二级评论是指评论下的回复
ENABLE_GET_SUB_COMMENTS = False

# 单个视频评论的最大数量，0表示不限制
# 如果视频评论数量很大，可以设置此值来限制爬取数量
PER_NOTE_MAX_COMMENTS_COUNT = 0

# ==================== 日志配置 ====================
# 是否开启日志打印输出到文件中
ENABLE_LOG_FILE = True

# ==================== 断点续爬配置 ====================
# 是否启用断点续爬功能
# 开启后，如果爬虫中断，可以从上次中断的位置继续爬取
ENABLE_CHECKPOINT = True

# 指定断点续爬的检查点ID，如果为空，则加载最新的检查点
SPECIFIED_CHECKPOINT_ID = ""

# 检查点存储类型，支持 file 和 redis
CHECKPOINT_STORAGE_TYPE = "file"  # file or redis

# ==================== 请求控制配置 ====================
# 爬虫请求间隔时间，单位：秒，默认1秒
# ⚠️⚠️⚠️ 重要：请勿设置过小，应最大限度减少对平台的压力
# 仅用于学习python爬虫技术
CRAWLER_TIME_SLEEP = 1

# ==================== 签名配置 ====================
# 签名类型：javascript
# 使用JavaScript方式生成请求签名
SIGN_TYPE = os.getenv("SIGN_TYPE", "javascript")

# ==================== 抖音特定配置 ====================
# 指定抖音需要爬取的视频ID列表（aweme_id）
# 当 CRAWLER_TYPE = "detail" 时使用
DY_SPECIFIED_ID_LIST = [
    # "7566756334578830627",
    # "7525538910311632128",
    # 可以添加更多视频ID
]

# 指定抖音创作者ID列表（sec_user_id）
# 当 CRAWLER_TYPE = "creator" 时使用
# 注意：这是抖音的sec_user_id，不是用户昵称
DY_CREATOR_ID_LIST = [
    # "MS4wLjABAAAAA7s_PXnCPdc5_t4p7NkHeomoz7TuXOIKkKt0XkYj6XA",
    # 可以添加更多创作者ID
]

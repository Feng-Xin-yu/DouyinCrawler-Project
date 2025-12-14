# -*- coding: utf-8 -*-
"""
命令行参数解析
使用typer库解析命令行参数，提供友好的命令行接口
"""

import sys
from enum import Enum

import typer
from typing_extensions import Annotated

import config
import constant


class CrawlerTypeEnum(str, Enum):
    """
    爬虫类型枚举
    """
    SEARCH = constant.CRALER_TYPE_SEARCH  # 关键词搜索
    DETAIL = constant.CRALER_TYPE_DETAIL  # 视频详情
    CREATOR = constant.CRALER_TYPE_CREATOR  # 创作者主页
    HOMEFEED = constant.CRALER_TYPE_HOMEFEED  # 首页推荐


class SaveDataOptionEnum(str, Enum):
    """
    数据保存选项枚举
    """
    CSV = "csv"
    JSON = "json"


def parse_cmd():
    """
    解析命令行参数并更新配置
    
    这个函数使用typer库提供友好的命令行接口，
    支持通过命令行参数覆盖配置文件中的设置
    """
    def main(
        crawler_type: Annotated[
            CrawlerTypeEnum,
            typer.Option(
                "--type",
                help="🔍 爬虫类型 (search=关键词搜索, detail=视频详情, creator=创作者主页, homefeed=首页推荐)"
            )
        ] = CrawlerTypeEnum.SEARCH,

        enable_checkpoint: Annotated[
            bool,
            typer.Option(
                "--enable_checkpoint/--no-enable_checkpoint",
                help="💾 是否启用断点续爬功能"
            )
        ] = config.ENABLE_CHECKPOINT,

        checkpoint_id: Annotated[
            str,
            typer.Option(
                "--checkpoint_id",
                help="🔖 指定断点续爬的检查点ID，如果为空则加载最新的检查点"
            )
        ] = config.SPECIFIED_CHECKPOINT_ID,

        keywords: Annotated[
            str,
            typer.Option(
                "--keywords",
                help="🔤 搜索关键词，多个关键词用逗号分隔"
            )
        ] = config.KEYWORDS,

    ):
        """
        🚀 DouyinCrawler - 抖音数据爬虫工具
        
        专门用于爬取抖音平台的数据，支持搜索、详情、创作者、首页推荐等功能。
        
        [bold green]示例用法:[/bold green]
        
        • 爬取搜索结果：
          python main.py --type search --keywords "Python,爬虫"
        
        • 启用断点续爬：
          python main.py --type creator --enable_checkpoint
        
        • 禁用断点续爬：
          python main.py --type detail --no-enable_checkpoint
        """
        # 更新全局配置，保持与原有逻辑的兼容性
        config.CRAWLER_TYPE = crawler_type.value
        config.KEYWORDS = keywords
        config.ENABLE_CHECKPOINT = enable_checkpoint
        config.SPECIFIED_CHECKPOINT_ID = checkpoint_id

    # 检查是否是帮助命令
    if '--help' in sys.argv or '-h' in sys.argv:
        # 如果是帮助命令，直接运行 typer 并退出
        typer.run(main)
        return

    # 使用 typer.run 但捕获 SystemExit 以避免程序提前退出
    try:
        typer.run(main)
    except SystemExit as e:
        # 如果是参数错误导致的退出，重新抛出
        if e.code != 0:
            raise
        # 如果是正常的参数解析完成，继续执行后续代码
        pass

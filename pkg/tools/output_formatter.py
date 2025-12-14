# -*- coding: utf-8 -*-
"""
输出格式化工具
提供美观、统一的控制台输出格式
"""

import sys
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger


class OutputFormatter:
    """
    输出格式化类
    提供统一的输出格式，包括进度显示、断点信息等
    """
    
    # 使用简单的文本标记
    SUCCESS = "[成功]"
    ERROR = "[错误]"
    WARNING = "[警告]"
    INFO = "[信息]"
    PROGRESS = "[进度]"
    CHECKPOINT = "[断点]"
    ACCOUNT = "[账号]"
    VIDEO = "[视频]"
    COMMENT = "[评论]"
    
    @staticmethod
    def print_header(title: str, subtitle: str = ""):
        """
        打印标题头部
        
        Args:
            title: 主标题
            subtitle: 副标题（可选）
        """
        print("\n" + "=" * 80)
        print(f"  {title}")
        if subtitle:
            print(f"  {subtitle}")
        print("=" * 80 + "\n")
    
    @staticmethod
    def print_section(title: str):
        """
        打印章节标题
        
        Args:
            title: 章节标题
        """
        print(f"\n{'─' * 60}")
        print(f"  {title}")
        print(f"{'─' * 60}\n")
    
    @staticmethod
    def print_info(message: str, icon: str = "[信息]"):
        """
        打印信息
        
        Args:
            message: 消息内容
            icon: 标记（可选）
        """
        print(f"{icon} {message}")
    
    @staticmethod
    def print_success(message: str):
        """
        打印成功消息
        
        Args:
            message: 消息内容
        """
        print(f"{OutputFormatter.SUCCESS} {message}")
    
    @staticmethod
    def print_error(message: str):
        """
        打印错误消息
        
        Args:
            message: 消息内容
        """
        print(f"{OutputFormatter.ERROR} {message}")
    
    @staticmethod
    def print_warning(message: str):
        """
        打印警告消息
        
        Args:
            message: 消息内容
        """
        print(f"{OutputFormatter.WARNING} {message}")
    
    @staticmethod
    def print_progress(
        current: int,
        total: int,
        item_type: str = "项",
        prefix: str = "进度",
        show_percentage: bool = True
    ):
        """
        打印进度信息
        
        Args:
            current: 当前数量
            total: 总数量
            item_type: 项目类型（如"视频"、"评论"）
            prefix: 前缀文本
            show_percentage: 是否显示百分比
        """
        if total == 0:
            percentage = 0
        else:
            percentage = (current / total) * 100
        
        if show_percentage:
            print(f"{OutputFormatter.PROGRESS} {prefix}: {current}/{total} {item_type} ({percentage:.1f}%)")
        else:
            print(f"{OutputFormatter.PROGRESS} {prefix}: {current}/{total} {item_type}")
    
    @staticmethod
    def print_checkpoint_info(checkpoint_data: Dict):
        """
        打印断点信息
        
        Args:
            checkpoint_data: 断点数据字典
        """
        print(f"\n{OutputFormatter.CHECKPOINT} 断点信息:")
        print(f"  • 断点ID: {checkpoint_data.get('id', '未知')}")
        print(f"  • 平台: {checkpoint_data.get('platform', '未知')}")
        print(f"  • 模式: {checkpoint_data.get('mode', '未知')}")
        
        # 根据模式显示不同的断点信息
        mode = checkpoint_data.get('mode', '')
        if mode == 'creator':
            creator_id = checkpoint_data.get('current_creator_id', '')
            page = checkpoint_data.get('current_creator_page', '0')
            if creator_id:
                # 限制显示长度
                display_id = creator_id[:30] + "..." if len(creator_id) > 30 else creator_id
                print(f"  • 当前创作者: {display_id}")
            if page and page != '0':
                print(f"  • 当前页码: {page}")
        elif mode == 'search':
            keyword = checkpoint_data.get('current_search_keyword', '')
            page = checkpoint_data.get('current_search_page', 1)
            search_id = checkpoint_data.get('current_search_id', '')
            if keyword:
                print(f"  • 当前关键词: {keyword}")
            if page and page > 1:
                print(f"  • 当前页码: {page}")
            if search_id:
                print(f"  • 搜索ID: {search_id[:20]}...")
        elif mode == 'homefeed':
            refresh_index = checkpoint_data.get('current_homefeed_note_index', 0)
            if refresh_index:
                print(f"  • 当前刷新索引: {refresh_index}")
        
        # 显示已爬取数量
        notes = checkpoint_data.get('crawled_note_list', [])
        if notes:
            crawled_count = len([n for n in notes if n.get('is_success_crawled', False)])
            print(f"  • 已爬取数量: {crawled_count}")
    
    @staticmethod
    def print_resume_info(checkpoint_data: Dict):
        """
        打印断点续爬信息
        
        Args:
            checkpoint_data: 断点数据字典
        """
        print(f"\n{OutputFormatter.CHECKPOINT} 从断点继续爬取:")
        mode = checkpoint_data.get('mode', '')
        
        if mode == 'creator':
            creator_id = checkpoint_data.get('current_creator_id', '')
            page = checkpoint_data.get('current_creator_page', '0')
            if creator_id:
                print(f"  • 继续从创作者: {creator_id}")
            if page and page != '0':
                print(f"  • 继续从页码: {page}")
        elif mode == 'search':
            keyword = checkpoint_data.get('current_search_keyword', '')
            page = checkpoint_data.get('current_search_page', 1)
            if keyword:
                print(f"  • 继续从关键词: {keyword}")
            if page and page > 1:
                print(f"  • 继续从页码: {page}")
        elif mode == 'homefeed':
            refresh_index = checkpoint_data.get('current_homefeed_note_index', 0)
            if refresh_index:
                print(f"  • 继续从刷新索引: {refresh_index}")
        
        notes = checkpoint_data.get('crawled_note_list', [])
        if notes:
            crawled_count = len([n for n in notes if n.get('is_success_crawled', False)])
            print(f"  • 已爬取: {crawled_count} 项")
    
    @staticmethod
    def print_interrupt_info(
        reason: str,
        checkpoint_data: Optional[Dict] = None,
        stats: Optional[Dict] = None
    ):
        """
        打印中断信息
        
        Args:
            reason: 中断原因
            checkpoint_data: 断点数据（可选）
            stats: 统计信息（可选）
        """
        print("\n" + "=" * 80)
        print(f"{OutputFormatter.WARNING} 爬虫中断")
        print("=" * 80)
        print(f"\n中断原因: {reason}")
        
        if checkpoint_data:
            print("\n当前断点状态:")
            OutputFormatter.print_checkpoint_info(checkpoint_data)
        
        if stats:
            print("\n爬取统计:")
            for key, value in stats.items():
                print(f"  • {key}: {value}")
        
        print("\n" + "=" * 80)
        print("[提示] 下次运行时会从断点继续爬取（如果启用了断点续爬功能）")
        print("=" * 80 + "\n")
    
    @staticmethod
    def print_crawler_start(
        crawler_type: str,
        config_info: Dict
    ):
        """
        打印爬虫启动信息
        
        Args:
            crawler_type: 爬取类型
            config_info: 配置信息字典
        """
        OutputFormatter.print_header("DouyinCrawler 启动", f"爬取类型: {crawler_type}")
        
        print(f"{OutputFormatter.INFO} 配置信息:")
        for key, value in config_info.items():
            print(f"  • {key}: {value}")
    
    @staticmethod
    def print_crawler_summary(stats: Dict):
        """
        打印爬虫总结信息
        
        Args:
            stats: 统计信息字典
        """
        OutputFormatter.print_header("爬取完成", "统计信息")
        
        for key, value in stats.items():
            print(f"  • {key}: {value}")
        
        print("\n" + "=" * 80 + "\n")
    
    @staticmethod
    def print_account_info(account_name: str, status: str = "正常"):
        """
        打印账号信息
        
        Args:
            account_name: 账号名称
            status: 账号状态
        """
        status_mark = "[正常]" if status == "正常" else "[警告]"
        print(f"{OutputFormatter.ACCOUNT} 当前账号: {account_name} ({status_mark} {status})")
    
    @staticmethod
    def print_video_info(aweme_id: str, title: str = "", action: str = "爬取"):
        """
        打印视频信息
        
        Args:
            aweme_id: 视频ID
            title: 视频标题（可选）
            action: 操作类型（爬取/跳过等）
        """
        if title:
            # 限制标题长度
            if len(title) > 50:
                title = title[:47] + "..."
            print(f"{OutputFormatter.VIDEO} {action}: {aweme_id} - {title}")
        else:
            print(f"{OutputFormatter.VIDEO} {action}: {aweme_id}")
    
    @staticmethod
    def print_comment_info(count: int, aweme_id: str = ""):
        """
        打印评论信息
        
        Args:
            count: 评论数量
            aweme_id: 视频ID（可选）
        """
        if aweme_id:
            print(f"{OutputFormatter.COMMENT} 视频 {aweme_id}: 爬取 {count} 条评论")
        else:
            print(f"{OutputFormatter.COMMENT} 爬取 {count} 条评论")

# -*- coding: utf-8 -*-
"""
DouyinCrawler 主入口文件
程序的启动入口，负责初始化配置、启动爬虫等
"""

import asyncio
import sys

import cmd_arg
import config
import constant
from base.base_crawler import AbstractCrawler
from douyin import DouYinCrawler
from pkg.tools.utils import init_logging_config


class CrawlerFactory:
    """
    爬虫工厂类
    使用工厂模式创建爬虫实例
    
    设计思路：
    1. 使用字典存储平台名称和爬虫类的映射
    2. 通过平台名称创建对应的爬虫实例
    3. 便于扩展新的平台支持
    """
    CRAWLERS = {
        constant.DOUYIN_PLATFORM_NAME: DouYinCrawler,
    }

    @staticmethod
    def create_crawler(platform: str = constant.DOUYIN_PLATFORM_NAME) -> AbstractCrawler:
        """
        根据平台名称创建爬虫实例
        
        Args:
            platform: 平台名称，默认使用抖音平台
            
        Returns:
            AbstractCrawler: 爬虫实例
            
        Raises:
            ValueError: 如果平台名称无效
        """
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError(
                f"Invalid Media Platform. Currently only supported: {list(CrawlerFactory.CRAWLERS.keys())}"
            )
        return crawler_class()


async def main():
    """
    主函数
    程序的入口点，负责：
    1. 解析命令行参数
    2. 初始化日志配置
    3. 创建并启动爬虫
    """
    print(
        """
# [声明] 本代码仅供个人学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。
"""
    )

    # 解析命令行参数
    cmd_arg.parse_cmd()

    # 初始化日志配置
    init_logging_config()

    # 创建爬虫实例
    crawler = CrawlerFactory.create_crawler(platform=constant.DOUYIN_PLATFORM_NAME)
    
    # 异步初始化爬虫
    await crawler.async_initialize()
    
    # 启动爬虫
    try:
        await crawler.start()
    finally:
        # 清理爬虫资源（关闭HTTP客户端等）
        await crawler.cleanup()


if __name__ == "__main__":
    try:
        # 运行主函数
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        # 处理Ctrl+C中断
        from pkg.tools.output_formatter import OutputFormatter
        
        OutputFormatter.print_interrupt_info(
            reason="用户中断 (Ctrl+C)",
            checkpoint_data=None  # 断点信息会在handler中输出
        )
        sys.exit(0)
    except Exception as e:
        # 处理其他未捕获的异常
        from pkg.tools import utils
        
        print("\n" + "="*80)
        print("[错误] 程序发生未捕获的异常")
        print("="*80)
        
        # 使用优化的错误格式化
        error_msg = utils.format_error_message(e, context={
            "程序阶段": "主程序执行",
            "爬取类型": getattr(config, 'CRAWLER_TYPE', '未知'),
            "平台": constant.DOUYIN_PLATFORM_NAME,
        })
        print(error_msg)
        
        # 记录到日志
        utils.log_error_with_context(
            utils.logger,
            e,
            context={
                "程序阶段": "主程序执行",
                "爬取类型": getattr(config, 'CRAWLER_TYPE', '未知'),
            },
            level="CRITICAL"
        )
        
        # 记录完整堆栈
        utils.logger.opt(exception=True).critical("完整异常堆栈:")
        
        print("\n" + "="*80)
        print("[提示] 如果问题持续存在，请检查:")
        print("   1. 日志文件: logs/douyin/ 目录下的最新日志")
        print("   2. 配置文件: config/base_config.py")
        print("   3. 账号配置: config/accounts_cookies.xlsx")
        print("   4. 签名功能: 确保已安装 PyExecJS 依赖（pip install PyExecJS）")
        print("   5. JavaScript运行时: 确保已安装 Node.js")
        print("="*80)
        
        sys.exit(1)

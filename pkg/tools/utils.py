# -*- coding: utf-8 -*-
"""
工具函数主模块
提供日志初始化、字符串处理等通用工具函数
"""

import argparse
import os
import random
import sys
from random import Random

from loguru import logger as _loguru_logger

from .crawler_util import *
from .time_util import *


# 延迟初始化标志，避免与config模块的循环导入
_logger_initialized = False


def get_logger():
    """
    获取或初始化日志记录器（延迟加载，避免循环导入）
    
    Returns:
        Logger: loguru日志记录器实例
    """
    global _logger_initialized
    if _logger_initialized:
        return _loguru_logger

    # 在这里导入config，避免循环依赖
    import config

    # 移除默认处理器
    _loguru_logger.remove()

    # 缓存文件路径处理结果，避免重复计算
    _file_name_cache = {}
    
    def get_file_name(file_path):
        """获取文件名，使用缓存优化性能"""
        if file_path not in _file_name_cache:
            _file_name_cache[file_path] = os.path.basename(file_path)
        return _file_name_cache[file_path]
    
    # 自定义过滤器，添加位置字段（文件:函数:行号）
    def add_location(record):
        # 简化文件路径，只显示文件名（使用缓存优化）
        file_name = get_file_name(record['file'].name)
        location = f"{file_name}:{record['function']}:{record['line']}"
        record["extra"]["location"] = location
        return True

    # 添加控制台处理器，使用美观的格式
    # 使用更清晰的格式：时间 | 级别 | 位置 | 消息
    # 注意：不启用 backtrace 和 diagnose，避免每次日志都收集堆栈信息（性能优化）
    # 在需要完整堆栈时，使用 logger.opt(exception=True).error() 即可
    _loguru_logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[location]: <35}</cyan> | <level>{message}</level>",
        level="INFO",
        colorize=True,
        filter=add_location,
        # 移除 backtrace=True 和 diagnose=True，提升性能
        # 在需要完整堆栈时，使用 logger.opt(exception=True).error() 即可
    )

    # 如果启用了日志文件，添加文件处理器
    if config.ENABLE_LOG_FILE:
        # 创建logs目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, 'logs', 'douyin')  # 抖音爬虫使用固定的'douyin'目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = os.path.join(log_dir, f"{get_current_date()}.log")

        # 文件日志的自定义过滤器
        def add_location_file(record):
            location = f"{record['file'].name}:{record['function']}:{record['line']}"
            record["extra"]["location"] = location
            return True

        _loguru_logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[location]: <60} - {message}",
            level="INFO",
            encoding="utf-8",
            rotation="00:00",  # 每天午夜轮转
            retention="30 days",  # 保留30天的日志
            filter=add_location_file
        )

    _logger_initialized = True
    return _loguru_logger


# 属性式访问，用于向后兼容
class LoggerProxy:
    """
    日志代理对象，在首次访问时初始化日志记录器
    """
    def __getattr__(self, name):
        return getattr(get_logger(), name)


# 全局日志记录器实例
logger = LoggerProxy()


def init_logging_config():
    """
    初始化日志配置（用于向后兼容）
    
    Returns:
        Logger: 日志记录器实例
    """
    return get_logger()


def str2bool(v):
    """
    将字符串转换为布尔值
    
    Args:
        v: 字符串或布尔值
        
    Returns:
        bool: 布尔值
        
    Raises:
        argparse.ArgumentTypeError: 如果无法转换为布尔值
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def get_random_str(random_len: int = 12) -> str:
    """
    获取随机字符串
    
    Args:
        random_len: 字符串长度，默认12
        
    Returns:
        str: 随机字符串
    """
    random_str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    _random = Random()
    for _ in range(random_len):
        random_str += chars[_random.randint(0, length)]
    return random_str


def random_delay_time(min_time: int = 1, max_time: int = 3) -> int:
    """
    获取随机延迟时间（秒）
    
    Args:
        min_time: 最小延迟时间（秒），默认1
        max_time: 最大延迟时间（秒），默认3
        
    Returns:
        int: 随机延迟时间（秒）
    """
    return random.randint(min_time, max_time)


def format_error_message(exception: Exception, context: dict = None) -> str:
    """
    格式化错误消息，提供详细的错误信息
    
    性能优化：使用列表拼接而非字符串拼接，减少字符串操作开销
    
    Args:
        exception: 异常对象
        context: 上下文信息字典（可选）
        
    Returns:
        str: 格式化的错误消息
    """
    error_type = type(exception).__name__
    error_message = str(exception)
    
    # 构建详细的错误信息（使用列表，最后一次性join，性能更好）
    lines = [
        f"[错误] 错误类型: {error_type}",
        f"[信息] 错误信息: {error_message}",
    ]
    
    # 添加上下文信息
    if context:
        lines.append("\n[上下文] 上下文信息:")
        for key, value in context.items():
            # 限制值的长度，避免输出过长（性能优化：提前截断）
            value_str = str(value)
            if len(value_str) > 200:
                value_str = value_str[:200] + "..."
            lines.append(f"   • {key}: {value_str}")
    
    # 根据错误类型提供解决建议（使用小写比较，避免重复转换）
    error_msg_lower = error_message.lower()
    suggestions = []
    
    if "account" in error_msg_lower or "unauthorized" in error_msg_lower:
        suggestions.extend([
            "[提示] 解决建议:",
            "   1. 检查账号Cookie是否过期，需要重新提取",
            "   2. 检查账号是否被封禁，尝试更换账号",
            "   3. 检查config/accounts_cookies.xlsx中的账号配置是否正确",
        ])
    elif "rate limited" in error_msg_lower or "429" in error_message:
        suggestions.extend([
            "[提示] 解决建议:",
            "   1. 请求过于频繁，等待一段时间后重试",
            "   2. 增加CRAWLER_TIME_SLEEP配置，降低请求频率",
            "   3. 使用更多账号进行轮换",
        ])
    elif "connection" in error_msg_lower or "network" in error_msg_lower:
        suggestions.extend([
            "[提示] 解决建议:",
            "   1. 检查网络连接是否正常",
            "   2. 检查代理IP是否可用",
            "   3. 检查签名服务是否正常运行（端口8989）",
        ])
    elif "proxy" in error_msg_lower:
        suggestions.extend([
            "[提示] 解决建议:",
            "   1. 检查代理IP配置是否正确",
            "   2. 检查代理IP是否可用",
            "   3. 尝试更换代理IP",
        ])
    elif "checkpoint" in error_msg_lower:
        suggestions.extend([
            "[提示] 解决建议:",
            "   1. 检查断点文件是否存在且格式正确",
            "   2. 检查data/checkpoints目录是否有写入权限",
            "   3. 如果断点文件损坏，可以删除后重新开始",
        ])
    
    if suggestions:
        lines.append("")
        lines.extend(suggestions)
    
    # 一次性join，性能更好
    return "\n".join(lines)


def log_error_with_context(logger, exception: Exception, context: dict = None, level: str = "ERROR"):
    """
    记录带上下文的错误信息
    
    Args:
        logger: 日志记录器
        exception: 异常对象
        context: 上下文信息字典
        level: 日志级别，默认为ERROR
    """
    error_msg = format_error_message(exception, context)
    
    # 根据级别记录日志（使用 opt(exception=True) 获取完整堆栈，但不影响正常日志性能）
    if level.upper() == "ERROR":
        logger.error(error_msg)
        # 只在错误时记录完整堆栈
        logger.opt(exception=True).error("完整异常堆栈:")
    elif level.upper() == "WARNING":
        logger.warning(error_msg)
        logger.opt(exception=True).warning("完整异常堆栈:")
    elif level.upper() == "CRITICAL":
        logger.critical(error_msg)
        logger.opt(exception=True).critical("完整异常堆栈:")
    else:
        logger.error(error_msg)
        logger.opt(exception=True).error("完整异常堆栈:")

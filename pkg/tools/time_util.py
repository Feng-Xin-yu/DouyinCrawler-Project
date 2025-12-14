# -*- coding: utf-8 -*-
"""
时间工具函数模块
提供时间戳、日期时间字符串转换等时间处理功能
"""

import time
from datetime import datetime, timedelta, timezone


def get_current_timestamp() -> int:
    """
    获取当前的时间戳（13位毫秒级）
    
    Returns:
        int: 当前时间戳，例如：1701493264496
    """
    return int(time.time() * 1000)


def get_current_time(time_format: str = "%Y-%m-%d %X") -> str:
    """
    获取当前的时间字符串
    
    Args:
        time_format: 时间格式，默认 "%Y-%m-%d %X"
        
    Returns:
        str: 格式化的时间字符串，例如：'2023-12-02 13:01:23'
    """
    return time.strftime(time_format, time.localtime())


def get_current_date() -> str:
    """
    获取当前的日期字符串
    
    Returns:
        str: 日期字符串，例如：'2023-12-02'
    """
    return time.strftime('%Y-%m-%d', time.localtime())


def get_time_str_from_unix_time(unixtime):
    """
    将Unix时间戳转换为字符串日期时间
    
    Args:
        unixtime: Unix时间戳（秒级或毫秒级）
        
    Returns:
        str: 日期时间字符串，例如：'2023-12-02 13:01:23'
    """
    # 如果是毫秒级时间戳，转换为秒级
    if int(unixtime) > 1000000000000:
        unixtime = int(unixtime) / 1000
    return time.strftime('%Y-%m-%d %X', time.localtime(unixtime))


def get_date_str_from_unix_time(unixtime):
    """
    将Unix时间戳转换为字符串日期
    
    Args:
        unixtime: Unix时间戳（秒级或毫秒级）
        
    Returns:
        str: 日期字符串，例如：'2023-12-02'
    """
    # 如果是毫秒级时间戳，转换为秒级
    if int(unixtime) > 1000000000000:
        unixtime = int(unixtime) / 1000
    return time.strftime('%Y-%m-%d', time.localtime(unixtime))


def get_unix_time_from_time_str(time_str):
    """
    将字符串时间转换为Unix时间戳（秒级）
    
    Args:
        time_str: 时间字符串，格式：'2023-12-02 13:01:23'
        
    Returns:
        int: Unix时间戳（秒级），转换失败返回0
    """
    try:
        format_str = "%Y-%m-%d %H:%M:%S"
        tm_object = time.strptime(str(time_str), format_str)
        return int(time.mktime(tm_object))
    except Exception:
        return 0


def get_unix_timestamp():
    """
    获取当前Unix时间戳（秒级）
    
    Returns:
        int: 当前Unix时间戳（秒级）
    """
    return int(time.time())


def rfc2822_to_china_datetime(rfc2822_time):
    """
    将RFC 2822格式时间字符串转换为中国时区的datetime对象
    
    Args:
        rfc2822_time: RFC 2822格式时间字符串，例如：'Sat Dec 23 17:12:54 +0800 2023'
        
    Returns:
        datetime: 中国时区的datetime对象
    """
    # 定义RFC 2822格式
    rfc2822_format = "%a %b %d %H:%M:%S %z %Y"
    
    # 将RFC 2822时间字符串转换为datetime对象
    dt_object = datetime.strptime(rfc2822_time, rfc2822_format)
    
    # 将datetime对象的时区转换为中国时区（UTC+8）
    dt_object_china = dt_object.astimezone(timezone(timedelta(hours=8)))
    return dt_object_china


def rfc2822_to_timestamp(rfc2822_time):
    """
    将RFC 2822格式时间字符串转换为Unix时间戳（秒级）
    
    Args:
        rfc2822_time: RFC 2822格式时间字符串，例如：'Sat Dec 23 17:12:54 +0800 2023'
        
    Returns:
        int: Unix时间戳（秒级）
    """
    # 定义RFC 2822格式
    rfc2822_format = "%a %b %d %H:%M:%S %z %Y"
    
    # 将RFC 2822时间字符串转换为datetime对象
    dt_object = datetime.strptime(rfc2822_time, rfc2822_format)
    
    # 将datetime对象转换为UTC时间
    dt_utc = dt_object.replace(tzinfo=timezone.utc)
    
    # 计算UTC时间对应的Unix时间戳
    timestamp = int(dt_utc.timestamp())
    
    return timestamp

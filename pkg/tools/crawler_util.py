# -*- coding: utf-8 -*-
"""
爬虫工具函数模块
提供爬虫相关的工具函数，如User-Agent生成、Cookie转换、URL解析等
"""

import base64
import random
import re
import urllib.parse
from io import BytesIO
from typing import Dict

from PIL import Image, ImageDraw


def show_qrcode(qr_code) -> None:
    """
    解析并显示base64编码的二维码图片
    
    Args:
        qr_code: base64编码的二维码图片字符串
    """
    # 如果包含逗号，说明是data URI格式，提取base64部分
    if "," in qr_code:
        qr_code = qr_code.split(",")[1]
    
    # 解码base64字符串
    qr_code = base64.b64decode(qr_code)
    # 打开图片
    image = Image.open(BytesIO(qr_code))

    # 在二维码周围添加白色边框，提高扫描准确率
    width, height = image.size
    new_image = Image.new('RGB', (width + 20, height + 20), color=(255, 255, 255))
    new_image.paste(image, (10, 10))
    draw = ImageDraw.Draw(new_image)
    draw.rectangle((0, 0, width + 19, height + 19), outline=(0, 0, 0), width=1)
    # 显示图片
    new_image.show()


def get_user_agent() -> str:
    """
    随机获取一个桌面浏览器的User-Agent
    
    Returns:
        str: User-Agent字符串
    """
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.5112.79 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.5060.53 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.4844.84 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5112.79 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5060.53 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.4844.84 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5112.79 Safari/537.36"
    ]
    return random.choice(ua_list)


def get_mobile_user_agent() -> str:
    """
    随机获取一个移动设备的User-Agent
    
    Returns:
        str: User-Agent字符串
    """
    ua_list = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/114.0.5735.99 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/114.0.5735.124 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/21.0 Chrome/110.0.5481.154 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 OPR/99.0.0.0",
        "Mozilla/5.0 (Linux; Android 10; JNY-LX1; HMSCore 6.11.0.302) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 HuaweiBrowser/13.0.5.303 Mobile Safari/537.36"
    ]
    return random.choice(ua_list)


def convert_str_cookie_to_dict(cookie_str: str) -> Dict:
    """
    将Cookie字符串转换为字典格式
    
    Args:
        cookie_str: Cookie字符串，例如：'name=value; path=/; domain=example.com'
        
    Returns:
        Dict: Cookie字典，例如：{'name': 'value', 'path': '/', 'domain': 'example.com'}
    """
    cookie_dict: Dict[str, str] = dict()
    if not cookie_str:
        return cookie_dict
    
    # 按分号分割Cookie字符串
    for cookie in cookie_str.split(";"):
        cookie = cookie.strip()
        if not cookie:
            continue
        # 按等号分割键值对
        cookie_list = cookie.split("=")
        if len(cookie_list) != 2:
            continue
        cookie_value = cookie_list[1]
        # 如果值是列表，转换为字符串
        if isinstance(cookie_value, list):
            cookie_value = "".join(cookie_value)
        cookie_dict[cookie_list[0]] = cookie_value
    return cookie_dict


def match_interact_info_count(count_str: str) -> int:
    """
    从字符串中提取数字（用于提取点赞数、评论数等）
    
    Args:
        count_str: 包含数字的字符串，例如：'1.2万'、'1234'
        
    Returns:
        int: 提取的数字，如果提取失败返回0
    """
    if not count_str:
        return 0

    # 使用正则表达式提取数字
    match = re.search(r'\d+', count_str)
    if match:
        number = match.group()
        return int(number)
    else:
        return 0


def extract_text_from_html(html: str) -> str:
    """
    从HTML中提取纯文本，移除所有HTML标签
    
    Args:
        html: HTML字符串
        
    Returns:
        str: 提取的纯文本
    """
    if not html:
        return ""
    
    # 移除script和style标签及其内容
    clean_html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
    # 移除所有其他HTML标签
    clean_text = re.sub(r'<[^>]+>', '', clean_html).strip()
    return clean_text


def extract_url_params_to_dict(url: str) -> Dict:
    """
    从URL中提取查询参数并转换为字典
    
    Args:
        url: URL字符串，例如：'https://example.com?key1=value1&key2=value2'
        
    Returns:
        Dict: 参数字典，例如：{'key1': 'value1', 'key2': 'value2'}
    """
    url_params_dict = dict()
    if not url:
        return url_params_dict
    
    # 解析URL
    parsed_url = urllib.parse.urlparse(url)
    # 解析查询参数
    url_params_dict = dict(urllib.parse.parse_qsl(parsed_url.query))
    return url_params_dict

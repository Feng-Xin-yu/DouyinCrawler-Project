# -*- coding: utf-8 -*-
"""
上下文变量模块
使用ContextVar实现线程安全的上下文变量，用于在异步环境中传递数据
"""

from contextvars import ContextVar

# 请求关键词上下文变量（用于记录当前请求的关键词）
request_keyword_var: ContextVar[str] = ContextVar("request_keyword", default="")

# 爬虫类型上下文变量（用于记录当前爬虫类型：search/detail/creator/homefeed）
crawler_type_var: ContextVar[str] = ContextVar("crawler_type", default="")

# 数据源关键词上下文变量（用于记录数据来源关键词）
source_keyword_var: ContextVar[str] = ContextVar("source_keyword", default="")

# -*- coding: utf-8 -*-
"""
代理IP配置模块
配置代理IP池相关参数
"""

import os

# ==================== 代理IP开关 ====================
# 是否开启 IP 代理
# 开启后，爬虫会使用代理IP来发送请求，降低被封禁的风险
ENABLE_IP_PROXY = True

# ==================== 代理IP池配置 ====================
# 代理IP池数量
# 一般情况下设置成2个就够了，程序会自动维护IP可用性
# 程序会自动检测IP是否可用，不可用时会自动更换
IP_PROXY_POOL_COUNT = 2

# 代理IP提供商名称
# 目前支持：kuaidaili（快代理）
IP_PROXY_PROVIDER_NAME = "kuaidaili"

# ==================== 快代理配置 ====================
# 快代理（https://www.kuaidaili.com/）的配置信息
# 可以通过环境变量设置，如果没有设置则需要手动填写
# ⚠️ 注意：需要先购买快代理的服务才能使用
KDL_SECERT_ID = os.getenv("KDL_SECERT_ID", "你的快代理secert_id")
KDL_SIGNATURE = os.getenv("KDL_SIGNATURE", "你的快代理签名")
KDL_USER_NAME = os.getenv("KDL_USER_NAME", "你的快代理用户名")
KDL_USER_PWD = os.getenv("KDL_USER_PWD", "你的快代理密码")

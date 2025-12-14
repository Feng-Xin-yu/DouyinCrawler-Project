# -*- coding: utf-8 -*-
"""
数据模型模块
定义抖音数据的数据结构
"""

from .m_douyin import DouyinAweme, DouyinAwemeComment, DouyinCreator
from .m_checkpoint import Checkpoint, CheckpointNote

__all__ = ['DouyinAweme', 'DouyinAwemeComment', 'DouyinCreator', 'Checkpoint']

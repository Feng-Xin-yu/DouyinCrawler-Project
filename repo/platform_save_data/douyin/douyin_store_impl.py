# -*- coding: utf-8 -*-
"""
抖音存储实现类
提供CSV、JSON两种存储方式的实现
"""

import asyncio
import csv
import json
import os
import pathlib
from typing import Dict

import aiofiles

import config
from base.base_crawler import AbstractStore
from pkg.tools import utils
from var import crawler_type_var



def calculate_number_of_files(file_store_path: str) -> int:
    """
    计算数据保存文件的前部分排序数字
    支持每次运行代码不写到同一个文件中
    
    Args:
        file_store_path: 文件存储路径
        
    Returns:
        int: 文件编号
    """
    if not os.path.exists(file_store_path):
        return 1
    try:
        return (
            max(
                [
                    int(file_name.split("_")[0])
                    for file_name in os.listdir(file_store_path)
                    if file_name.split("_")[0].isdigit()
                ]
            )
            + 1
        )
    except (ValueError, IndexError):
        return 1


class DouyinCsvStoreImplement(AbstractStore):
    """
    CSV存储实现
    将数据保存为CSV文件格式
    """
    csv_store_path: str = "data/douyin"
    file_count: int = calculate_number_of_files(csv_store_path)

    def make_save_file_name(self, store_type: str) -> str:
        """
        生成保存文件名
        
        Args:
            store_type: 存储类型（contents/comments/creator）
            
        Returns:
            str: 文件名，例如：data/douyin/1_search_contents_20240114.csv
        """
        return f"{self.csv_store_path}/{self.file_count}_{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.csv"

    async def save_data_to_csv(self, save_item: Dict, store_type: str):
        """
        将数据保存到CSV文件
        
        Args:
            save_item: 要保存的数据字典
            store_type: 存储类型（contents/comments/creator）
        """
        # 创建目录
        pathlib.Path(self.csv_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.make_save_file_name(store_type=store_type)
        
        # 异步写入CSV文件
        async with aiofiles.open(
            save_file_name, mode="a+", encoding="utf-8-sig", newline=""
        ) as f:
            writer = csv.writer(f)
            # 如果是新文件，先写入表头
            if await f.tell() == 0:
                await writer.writerow(save_item.keys())
            # 写入数据行
            await writer.writerow(save_item.values())

    async def store_content(self, content_item: Dict):
        """
        存储视频内容（CSV格式）
        
        Args:
            content_item: 视频数据字典
        """
        await self.save_data_to_csv(save_item=content_item, store_type="contents")

    async def store_comment(self, comment_item: Dict):
        """
        存储评论（CSV格式）
        
        Args:
            comment_item: 评论数据字典
        """
        await self.save_data_to_csv(save_item=comment_item, store_type="comments")

    async def store_creator(self, creator: Dict):
        """
        存储创作者信息（CSV格式）
        
        Args:
            creator: 创作者数据字典
        """
        await self.save_data_to_csv(save_item=creator, store_type="creator")


class DouyinJsonStoreImplement(AbstractStore):
    """
    JSON存储实现
    将数据保存为JSON文件格式
    """
    json_store_path: str = "data/douyin/json"
    lock = asyncio.Lock()
    file_count: int = calculate_number_of_files(json_store_path)

    def make_save_file_name(self, store_type: str) -> str:
        """
        生成保存文件名
        
        Args:
            store_type: 存储类型（contents/comments/creator）
            
        Returns:
            str: 文件名，例如：data/douyin/json/search_contents_20240114.json
        """
        return f"{self.json_store_path}/{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.json"

    async def save_data_to_json(self, save_item: Dict, store_type: str):
        """
        将数据保存到JSON文件
        
        Args:
            save_item: 要保存的数据字典
            store_type: 存储类型（contents/comments/creator）
        """
        # 创建目录
        pathlib.Path(self.json_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.make_save_file_name(store_type=store_type)
        save_data = []

        # 使用锁保证线程安全
        async with self.lock:
            # 如果文件已存在，读取现有数据
            if os.path.exists(save_file_name):
                async with aiofiles.open(save_file_name, "r", encoding="utf-8") as file:
                    content = await file.read()
                    if content:
                        save_data = json.loads(content)

            # 添加新数据
            save_data.append(save_item)
            
            # 写入文件
            async with aiofiles.open(save_file_name, "w", encoding="utf-8") as file:
                await file.write(json.dumps(save_data, ensure_ascii=False, indent=2))

    async def store_content(self, content_item: Dict):
        """
        存储视频内容（JSON格式）
        
        Args:
            content_item: 视频数据字典
        """
        await self.save_data_to_json(content_item, "contents")

    async def store_comment(self, comment_item: Dict):
        """
        存储评论（JSON格式）
        
        Args:
            comment_item: 评论数据字典
        """
        await self.save_data_to_json(comment_item, "comments")

    async def store_creator(self, creator: Dict):
        """
        存储创作者信息（JSON格式）
        
        Args:
            creator: 创作者数据字典
        """
        await self.save_data_to_json(save_item=creator, store_type="creator")

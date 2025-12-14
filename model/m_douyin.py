# -*- coding: utf-8 -*-
"""
抖音数据模型
定义抖音视频、评论、创作者的数据结构
使用Pydantic进行数据验证和序列化
"""

from pydantic import BaseModel, Field


class DouyinAweme(BaseModel):
    """
    抖音视频数据模型
    存储视频的所有信息，包括视频内容、统计数据、作者信息等
    """
    # 视频基本信息
    aweme_id: str = Field(default="", description="视频ID")
    aweme_type: str = Field(default="", description="视频类型")
    title: str = Field(default="", description="视频标题")
    desc: str = Field(default="", description="视频描述")
    create_time: str = Field(default="", description="视频发布时间戳")
    
    # 视频统计数据
    liked_count: str = Field(default="", description="视频点赞数")
    comment_count: str = Field(default="", description="视频评论数")
    share_count: str = Field(default="", description="视频分享数")
    collected_count: str = Field(default="", description="视频收藏数")
    
    # 视频URL信息
    aweme_url: str = Field(default="", description="视频详情页URL")
    cover_url: str = Field(default="", description="视频封面图URL")
    video_download_url: str = Field(default="", description="视频下载地址")
    
    # 其他信息
    source_keyword: str = Field(default="", description="搜索来源关键字")
    is_ai_generated: int = Field(default=0, description="是否AI生成，0:否，1:是")
    
    # 作者信息
    user_id: str = Field(default="", description="用户ID")
    sec_uid: str = Field(default="", description="用户sec_uid（抖音的用户标识）")
    short_user_id: str = Field(default="", description="用户短ID")
    user_unique_id: str = Field(default="", description="用户唯一ID（昵称）")
    nickname: str = Field(default="", description="用户昵称")
    avatar: str = Field(default="", description="用户头像地址")
    user_signature: str = Field(default="", description="用户签名")
    ip_location: str = Field(default="", description="IP地址（发布视频时的位置）")


class DouyinAwemeComment(BaseModel):
    """
    抖音视频评论数据模型
    存储评论的所有信息，包括评论内容、统计数据、用户信息等
    """
    # 评论基本信息
    comment_id: str = Field(default="", description="评论ID")
    aweme_id: str = Field(default="", description="视频ID")
    content: str = Field(default="", description="评论内容")
    create_time: str = Field(default="", description="评论时间戳")
    
    # 评论统计数据
    sub_comment_count: str = Field(default="", description="评论回复数")
    like_count: str = Field(default="", description="点赞数")
    
    # 评论关系信息
    parent_comment_id: str = Field(default="", description="父评论ID（如果是回复）")
    reply_to_reply_id: str = Field(default="", description="目标评论ID（回复的评论ID）")
    
    # 评论其他信息
    pictures: str = Field(default="", description="评论图片列表（逗号分隔的URL）")
    ip_location: str = Field(default="", description="评论时的IP地址")
    
    # 评论用户信息
    user_id: str = Field(default="", description="用户ID")
    sec_uid: str = Field(default="", description="用户sec_uid")
    short_user_id: str = Field(default="", description="用户短ID")
    user_unique_id: str = Field(default="", description="用户唯一ID")
    nickname: str = Field(default="", description="用户昵称")
    avatar: str = Field(default="", description="用户头像地址")
    user_signature: str = Field(default="", description="用户签名")


class DouyinCreator(BaseModel):
    """
    抖音创作者数据模型
    存储创作者的所有信息，包括基本信息、统计数据等
    """
    # 创作者基本信息
    user_id: str = Field(default="", description="用户ID")
    nickname: str = Field(default="", description="用户昵称")
    avatar: str = Field(default="", description="用户头像地址")
    ip_location: str = Field(default="", description="IP地址")
    desc: str = Field(default="", description="用户描述/签名")
    gender: str = Field(default="", description="性别：未知/男/女")
    
    # 创作者统计数据
    follows: str = Field(default="", description="关注数")
    fans: str = Field(default="", description="粉丝数")
    interaction: str = Field(default="", description="获赞数")
    videos_count: str = Field(default="", description="作品数")

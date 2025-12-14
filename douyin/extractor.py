# -*- coding: utf-8 -*-
"""
抖音数据提取器
从API响应中提取和转换数据，将原始JSON数据转换为数据模型对象
"""

from typing import Dict, List, Optional

from model.m_douyin import DouyinAweme, DouyinAwemeComment, DouyinCreator


class DouyinExtractor:
    """
    抖音数据提取器
    负责从API响应的原始数据中提取结构化信息
    """
    
    def __init__(self):
        """
        初始化数据提取器
        """
        pass

    def _extract_video_download_url(self, aweme_detail: Dict) -> str:
        """
        提取视频下载地址
        从视频详情中提取可用的视频下载URL
        
        Args:
            aweme_detail: 视频详情字典
            
        Returns:
            str: 视频下载地址，如果提取失败返回空字符串
        """
        video_item = aweme_detail.get("video", {})
        # 尝试多种视频地址格式（按优先级）
        url_h264_list = video_item.get("play_addr_h264", {}).get("url_list", [])
        url_256_list = video_item.get("play_addr_256", {}).get("url_list", [])
        url_list = video_item.get("play_addr", {}).get("url_list", [])
        
        # 选择第一个可用的URL列表
        actual_url_list = url_h264_list or url_256_list or url_list
        
        # 通常URL列表的最后一个是最新的可用地址
        if not actual_url_list or len(actual_url_list) < 2:
            return ""
        return actual_url_list[-1]

    def _extract_content_cover_url(self, aweme_detail: Dict) -> str:
        """
        提取视频封面地址
        从视频详情中提取封面图URL
        
        Args:
            aweme_detail: 视频详情字典
            
        Returns:
            str: 视频封面地址，如果提取失败返回空字符串
        """
        video_item = aweme_detail.get("video", {})
        # 尝试raw_cover或origin_cover
        raw_cover_url_list = (
            video_item.get("raw_cover", {}) or video_item.get("origin_cover", {})
        ).get("url_list", [])
        
        # 通常URL列表的第二个是高清封面
        if raw_cover_url_list and len(raw_cover_url_list) > 1:
            return raw_cover_url_list[1]
        return ""

    def extract_aweme_from_dict(self, aweme_data: Dict) -> Optional[DouyinAweme]:
        """
        从API响应字典中提取视频信息
        这是对外接口，处理数据可能为空的情况
        
        Args:
            aweme_data: API响应的视频数据字典
            
        Returns:
            Optional[DouyinAweme]: 视频模型对象，如果数据为空返回None
        """
        if not aweme_data:
            return None
        return self._extract_aweme_from_dict(aweme_data)

    def _extract_aweme_from_dict(self, aweme_item: Dict) -> DouyinAweme:
        """
        内部方法：从字典提取视频信息
        处理视频数据的详细提取逻辑
        
        Args:
            aweme_item: 视频详情字典（可能包含aweme_info字段或直接是视频数据）
            
        Returns:
            DouyinAweme: 视频模型对象
        """
        # 处理数据格式：可能直接是视频数据，也可能在aweme_info字段中
        aweme_info = aweme_item.get("aweme_info", aweme_item)
        statistics = aweme_info.get("statistics", {})
        author_info = aweme_info.get("author", {})

        # 使用辅助方法提取视频和封面URL
        video_download_url = self._extract_video_download_url(aweme_info)
        cover_url = self._extract_content_cover_url(aweme_info)

        # 构建视频模型对象
        return DouyinAweme(
            aweme_id=str(aweme_info.get("aweme_id", "")),
            aweme_type=str(aweme_info.get("aweme_type", "")),
            title=aweme_info.get("preview_title", "") or aweme_info.get("desc", ""),
            desc=aweme_info.get("desc", ""),
            create_time=str(aweme_info.get("create_time", "")),
            liked_count=str(statistics.get("digg_count", "")),
            comment_count=str(statistics.get("comment_count", "")),
            share_count=str(statistics.get("share_count", "")),
            collected_count=str(statistics.get("collect_count", "")),
            aweme_url=f"https://www.douyin.com/video/{aweme_info.get('aweme_id', '')}",
            cover_url=cover_url,
            video_download_url=video_download_url,
            source_keyword="",  # 这个值会在handler中设置
            is_ai_generated=aweme_info.get("aigc_info", {}).get("aigc_label_type", 0),
            # 作者信息
            user_id=str(author_info.get("uid", "")),
            sec_uid=author_info.get("sec_uid", ""),
            short_user_id=str(author_info.get("short_id", "")),
            user_unique_id=author_info.get("unique_id", ""),
            nickname=author_info.get("nickname", ""),
            avatar=(
                author_info.get("avatar_thumb", {}).get("url_list", [""])[0]
                if author_info.get("avatar_thumb")
                else ""
            ),
            user_signature=author_info.get("signature", ""),
            ip_location=aweme_info.get("ip_label", ""),
        )

    def extract_comments_from_dict(
        self, aweme_id: str, comments_data: List[Dict]
    ) -> List[DouyinAwemeComment]:
        """
        从API响应中提取评论列表
        批量处理评论数据
        
        Args:
            aweme_id: 视频ID
            comments_data: 评论数据列表
            
        Returns:
            List[DouyinAwemeComment]: 评论模型对象列表
        """
        if not comments_data:
            return []

        result = []
        for comment_item in comments_data:
            comment = self._extract_comment_from_dict(aweme_id, comment_item)
            result.append(comment)
        return result

    def _extract_comment_image_list(self, comment_item: Dict) -> List[str]:
        """
        提取评论图片列表
        从评论数据中提取所有图片URL
        
        Args:
            comment_item: 评论数据字典
            
        Returns:
            List[str]: 图片URL列表
        """
        images_res = []
        image_list = comment_item.get("image_list", [])

        if not image_list:
            return []

        for image in image_list:
            image_url_list = image.get("origin_url", {}).get("url_list", [])
            if image_url_list and len(image_url_list) > 1:
                images_res.append(image_url_list[1])

        return images_res

    def _extract_comment_from_dict(
        self, aweme_id: str, comment_item: Dict
    ) -> DouyinAwemeComment:
        """
        内部方法：从字典提取评论信息
        处理单个评论数据的详细提取逻辑
        
        Args:
            aweme_id: 视频ID
            comment_item: 评论详情字典
            
        Returns:
            DouyinAwemeComment: 评论模型对象
        """
        user_info = comment_item.get("user", {})

        return DouyinAwemeComment(
            comment_id=str(comment_item.get("cid", "")),
            aweme_id=str(aweme_id),
            content=comment_item.get("text", ""),
            create_time=str(comment_item.get("create_time", "")),
            sub_comment_count=str(comment_item.get("reply_comment_total", "")),
            parent_comment_id=str(comment_item.get("reply_id", "") or ""),
            reply_to_reply_id=str(comment_item.get("reply_to_reply_id", "") or ""),
            like_count=str(comment_item.get("digg_count", "")),
            pictures=",".join(self._extract_comment_image_list(comment_item)),
            ip_location=comment_item.get("ip_label", ""),
            # 用户信息
            user_id=str(user_info.get("uid", "")),
            sec_uid=user_info.get("sec_uid", ""),
            short_user_id=str(user_info.get("short_id", "")),
            user_unique_id=user_info.get("unique_id", ""),
            nickname=user_info.get("nickname", ""),
            avatar=(
                user_info.get("avatar_thumb", {}).get("url_list", [""])[0]
                if user_info.get("avatar_thumb")
                else ""
            ),
            user_signature=user_info.get("signature", ""),
        )

    def extract_creator_from_dict(self, user_data: Dict) -> Optional[DouyinCreator]:
        """
        从API响应中提取创作者信息
        处理创作者数据的提取逻辑
        
        Args:
            user_data: 创作者数据字典
            
        Returns:
            Optional[DouyinCreator]: 创作者模型对象，如果数据为空返回None
        """
        if not user_data:
            return None

        # 处理数据格式：可能直接是用户数据，也可能在user字段中
        user_info = user_data.get("user", {}) or user_data
        statistics = user_info.get("statistics", {})

        # 性别映射：0-未知，1-男，2-女
        gender_map = {0: "未知", 1: "男", 2: "女"}

        return DouyinCreator(
            user_id=str(user_info.get("uid", "")),
            nickname=user_info.get("nickname", ""),
            avatar=(
                user_info.get("avatar_larger", {}).get("url_list", [""])[0]
                if user_info.get("avatar_larger")
                else ""
            ),
            ip_location=user_info.get("ip_location", ""),
            desc=user_info.get("signature", ""),
            gender=gender_map.get(user_info.get("gender", 0), "未知"),
            follows=str(statistics.get("following_count", "")),
            fans=str(statistics.get("follower_count", "")),
            interaction=str(statistics.get("total_favorited", "")),
            videos_count=str(statistics.get("aweme_count", "")),
        )

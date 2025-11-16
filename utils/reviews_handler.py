import aiohttp
from typing import Optional, Dict, List, Tuple
from astrbot.api import logger


class ReviewsHandler:
    """Steam评价数据处理器"""
    
    BASE_URL = "https://store.steampowered.com/appreviews/2807960"
    
    # 支持的语言列表
    LANGUAGES = {
        "all": "所有语言",
        "schinese": "简体中文",
        "tchinese": "繁体中文",
        "english": "英语",
        "german": "德语",
        "french": "法语",
        "italian": "意大利语",
        "indonesian": "印度尼西亚语",
        "japanese": "日语",
        "koreana": "韩语",
        "thai": "泰语",
        "spanish": "西班牙语-西班牙",
        "latam": "西班牙语-拉丁美洲",
        "portuguese": "葡萄牙语",
        "brazilian": "葡萄牙语-巴西"
        
    }
    
    # 评价描述中英映射表
    REVIEW_SCORE_DESC_MAP = {
        "Mostly Positive": "多半好评",
        "Mostly Negative": "多半差评",
        "Mixed": "褒贬不一",
        "Very Positive": "特别好评",
        "Positive": "好评",
        "Very Negative": "差评如潮",
        "Negative": "差评",
        "Overwhelmingly Positive": "好评如潮",
        "Overwhelmingly Negative": "差评如潮"
    }
    
    def __init__(self):
        self.session = None
    
    async def initialize(self, session: aiohttp.ClientSession):
        """初始化方法，设置session"""
        self.session = session
    
    async def get_single_language_reviews(self, language: str, timeout: int = 15) -> Optional[Dict]:
        """
        获取指定语言的评价数据
        
        Args:
            language: 语言代码
            timeout: 请求超时时间
            
        Returns:
            评价数据字典，失败时返回None
        """
        if self.session is None:
            logger.error("Session未初始化")
            return None
            
        params = {
            "json": 1,
            "filter": "updated",
            "language": language
        }
        
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with self.session.get(self.BASE_URL, params=params, timeout=timeout_obj) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success") == 1:
                        return result
                    else:
                        logger.error(f"获取{language}评价数据失败: {result}")
                        return None
                else:
                    logger.error(f"获取{language}评价数据失败，状态码: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"获取{language}评价数据异常: {str(e)}")
            return None
    
    async def get_all_languages_reviews(self, timeout: int = 15) -> Dict[str, Dict]:
        """
        并发获取所有语言的评价数据
        
        Args:
            timeout: 请求超时时间
            
        Returns:
            所有语言的评价数据字典
        """
        tasks = []
        for lang_code in self.LANGUAGES.keys():
            task = self.get_single_language_reviews(lang_code, timeout)
            tasks.append((lang_code, task))
        
        results = {}
        for lang_code, task in tasks:
            try:
                result = await task
                if result:
                    results[lang_code] = result
                else:
                    logger.warning(f"获取{lang_code}评价数据失败")
            except Exception as e:
                logger.error(f"获取{lang_code}评价数据异常: {str(e)}")
        
        return results
    
    def calculate_positive_rate(self, total_positive: int, total_reviews: int) -> str:
        """
        计算好评率
        
        Args:
            total_positive: 好评数
            total_reviews: 总评价数
            
        Returns:
            格式化的好评率字符串
        """
        if total_reviews == 0:
            return "0.00%"
        
        rate = (total_positive / total_reviews) * 100
        return f"{rate:.2f}%"
    
    def process_reviews_data(self, reviews_data: Dict[str, Dict]) -> Dict:
        """
        处理评价数据，提取所需信息并计算好评率
        
        Args:
            reviews_data: 原始评价数据
            
        Returns:
            处理后的评价统计数据
        """
        processed_data = {}
        
        for lang_code, data in reviews_data.items():
            if "query_summary" in data:
                summary = data["query_summary"]
                total_positive = summary.get("total_positive", 0)
                total_negative = summary.get("total_negative", 0)
                total_reviews = summary.get("total_reviews", 0)
                review_score_desc = summary.get("review_score_desc", "未知")
                
                # 使用映射表转换评价描述
                review_score_desc_cn = self.REVIEW_SCORE_DESC_MAP.get(review_score_desc, review_score_desc)
                
                # 计算好评率
                positive_rate = self.calculate_positive_rate(total_positive, total_reviews)
                
                processed_data[lang_code] = {
                    "language_name": self.LANGUAGES.get(lang_code, lang_code),
                    "total_positive": total_positive,
                    "total_negative": total_negative,
                    "total_reviews": total_reviews,
                    "positive_rate": positive_rate,
                    "review_score_desc": review_score_desc,
                    "review_score_desc_cn": review_score_desc_cn
                }
        
        return processed_data
    
    async def get_processed_reviews_data(self, timeout: int = 15) -> Dict:
        """
        获取并处理所有语言的评价数据
        
        Args:
            timeout: 请求超时时间
            
        Returns:
            处理后的评价统计数据
        """
        # 获取所有语言的评价数据
        reviews_data = await self.get_all_languages_reviews(timeout)
        
        # 处理数据
        processed_data = self.process_reviews_data(reviews_data)
        
        return processed_data
    
    def sort_languages_by_reviews(self, processed_data: Dict) -> List[Tuple[str, Dict]]:
        """
        按总评价数排序语言数据
        
        Args:
            processed_data: 处理后的评价数据
            
        Returns:
            按总评价数排序的语言数据列表
        """
        # 过滤掉"all"数据，因为它将单独显示
        filtered_data = {k: v for k, v in processed_data.items() if k != "all"}
        
        # 按总评价数降序排序
        sorted_data = sorted(filtered_data.items(), key=lambda x: x[1]["total_reviews"], reverse=True)
        
        return sorted_data
    
    async def get_reviews_data(self, timeout: int = 15) -> Dict:
        """
        获取所有语言的评价数据并返回格式化结果
        
        Args:
            timeout: 请求超时时间
            
        Returns:
            包含成功状态、all数据和languages数据的字典
        """
        try:
            # 获取并处理所有语言的评价数据
            processed_data = await self.get_processed_reviews_data(timeout)
            
            # 提取"all"数据
            all_data = processed_data.get("all", {})
            
            # 按总评价数排序其他语言数据
            sorted_languages = self.sort_languages_by_reviews(processed_data)
            
            return {
                "success": True,
                "all_data": all_data,
                "languages_data": sorted_languages
            }
        except Exception as e:
            logger.error(f"获取评价数据时出错: {str(e)}")
            return {
                "success": False,
                "message": f"获取评价数据失败: {str(e)}"
            }
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, StarTools, register
from astrbot.api.all import AstrBotConfig
from astrbot.api import logger

from typing import Union, Pattern
import aiohttp
from .utils.template import (
    reviews_html_builder,
)

from .utils.reviews_handler import ReviewsHandler


from typing import Dict, Any
from matplotlib.backends.backend_agg import FigureCanvasAgg

import aiohttp
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
@register("bf6_reviews", "chawu691", "查询战地6的steam各区的好评率", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""



    @filter.command("好评")
    async def reviews_command(self, event: AstrMessageEvent):
        """查询Steam游戏评价统计"""
        try:
            # 获取评价数据
            result = await self.reviews_handler.get_reviews_data()
            
            if result["success"]:
                # 生成HTML内容
                html_content = reviews_html_builder(result["all_data"], result["languages_data"])
                
                # 将HTML转换为图片
                image_url = await self.html_render(
                    html_content,
                    {},
                    True,
                    {
                        "timeout": 10000,
                        "quality": self.img_quality,
                        "clip": {"x": 0, "y": 0, "width": 2500, "height": 10000},
                    },
                )
                
                # 发送图片
                yield event.image_result(image_url)
            else:
                yield event.plain_result(result.get("message", "获取评价数据失败"))
                
        except Exception as e:
            logger.error(f"处理评价命令时出错: {str(e)}")
            yield event.plain_result(f"处理评价命令时出错: {str(e)}")

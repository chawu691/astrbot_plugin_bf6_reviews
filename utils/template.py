from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from astrbot.api import logger
from pathlib import Path
import time
import json

# 添加评价模板
REVIEWS_TEMPLATE = env.get_template("template_reviews.html")

def reviews_html_builder(all_data, languages_data):
    """
    构建评价统计html
    Args:
        all_data: 所有语言的评价数据
        languages_data: 按评价数排序的语言数据
    Returns:
        构建的Html
    """
    # 获取当前时间
    last_update = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    # 渲染HTML
    html = REVIEWS_TEMPLATE.render(
        all_data=all_data,
        languages_data=languages_data,
        last_update=last_update
    )
    
    return html

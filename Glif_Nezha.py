import os
import re
import json
import time
import requests
from io import BytesIO
from datetime import datetime, timedelta
import threading
from PIL import Image

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *
from config import conf

@plugins.register(
    name="Glif_Nezha",
    desire_priority=200,
    hidden=False,
    desc="A plugin for generating images using multiple Glif API models",
    version="1.0",
    author="Lingyuzhou",
)
class Glif_Nezha(Plugin):
    def __init__(self):
        super().__init__()
        try:
            conf = super().load_config()
            if not conf:
                raise Exception("配置未找到")
            
            # 从配置文件加载API token
            self.api_token = conf.get("api_token")
            if not self.api_token:
                raise Exception("在配置中未找到API令牌")
            
            # 定义触发词到模型ID的映射
            self.model_configs = {
                "cm6zapr9v0000stff1002b4fb": ["哪吒", "魔丸哪吒", "魔童哪吒"],
                "cm6zewimi0003fp45j09st0hx": ["灵珠", "灵珠哪吒", "正版哪吒"],
                "cm73qmq3d0000sg3muwfpnj6g": ["成年哪吒"],
                "cm73nyy8f000ah5gj83vxte5p": ["太乙", "太乙真人"],
                "cm73q06ll000ek0scgndiq0m5": ["申公豹"],                
                "cm70xa3790000vbuxa0dpjmbm": ["敖丙"],
                "cm73r5y5u0002ptoo61yajlyt": ["敖光"],                
                "cm70zms7l000113rg6dturhpl": ["敖闰"]
            }

            # 创建触发词到glif_id的反向映射
            self.trigger_to_id = {}
            for glif_id, triggers in self.model_configs.items():
                for trigger in triggers:
                    self.trigger_to_id[trigger] = glif_id
            
            # 设置图片保存目录和清理参数
            self.image_output_dir = "./plugins/Glif_Nezha/images"
            self.clean_interval = 3  # 天数
            self.clean_check_interval = 7200  # 秒数，每2小时检查一次

            # 创建图片保存目录
            if not os.path.exists(self.image_output_dir):
                os.makedirs(self.image_output_dir)
            
            # 注册消息处理器
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            
            # 启动定时清理任务
            self.schedule_next_run()
            
            logger.info("[Glif_Nezha] 插件初始化成功")
            
        except Exception as e:
            logger.error(f"[Glif_Nezha] 初始化失败: {e}")
            raise e

    def schedule_next_run(self):
        """安排下一次运行"""
        self.timer = threading.Timer(self.clean_check_interval, self.run_clean_task)
        self.timer.start()

    def run_clean_task(self):
        """运行清理任务并安排下一次运行"""
        self.clean_old_images()
        self.schedule_next_run()

    def clean_old_images(self):
        """清理指定天数前的图片"""
        logger.info(f"[Glif_Nezha] 开始检查是否需要清理旧图片，清理间隔：{self.clean_interval}天")
        now = datetime.now()
        cleaned_count = 0
        for filename in os.listdir(self.image_output_dir):
            file_path = os.path.join(self.image_output_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if now - file_time > timedelta(days=self.clean_interval):
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f"[Glif_Nezha] 已删除旧图片: {file_path}")
        if cleaned_count > 0:
            logger.info(f"[Glif_Nezha] 清理旧图片完成，共清理 {cleaned_count} 张图片")
        else:
            logger.info("[Glif_Nezha] 没有需要清理的旧图片")

    def download_and_save_image(self, image_url: str) -> str:
        """下载并保存图片"""
        logger.debug(f"[Glif_Nezha] 正在下载并保存图片: {image_url}")
        filename = f"{int(time.time())}.png"
        file_path = os.path.join(self.image_output_dir, filename)
        if self.download_image(image_url, file_path):
            logger.info(f"[Glif_Nezha] 图片已保存到 {file_path}")
            return file_path
        else:
            raise Exception('下载图片失败')

    def download_image(self, url, save_path):
        """下载并保存图片"""
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, verify=False, timeout=30)  # 禁用SSL验证
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    logger.debug(f"[Glif_Nezha] 图片已保存到: {save_path}")
                    return True
                else:
                    logger.error(f"[Glif_Nezha] 下载图片失败，HTTP状态码: {response.status_code}")
            except requests.exceptions.SSLError as e:
                logger.warning(f"[Glif_Nezha] SSL错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"[Glif_Nezha] 下载图片时发生错误: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise
        
        return False

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return
            
        content = e_context["context"].content
        
        # 检查是否使用了支持的触发词
        used_trigger = None
        for trigger in self.trigger_to_id.keys():
            if content.startswith(trigger):
                used_trigger = trigger
                break
                
        if not used_trigger:
            return
            
        logger.debug(f"[Glif_Nezha] 收到消息: {content}")
        
        try:
            # 移除触发词
            content = content[len(used_trigger):].strip()
            
            # 获取对应的glif_id
            glif_id = self.trigger_to_id[used_trigger]
            
             # 解析用户输入
            aspect = self.extract_aspect_ratio(content)
            content = self.clean_prompt_string(content)
            
            # 调用Glif API生成图片
            image_url = self.generate_image(content, aspect, glif_id)
            
            if image_url:
                # 下载并保存图片
                image_path = self.download_and_save_image(image_url)
                # 读取图片并转换为BytesIO对象
                with open(image_path, 'rb') as f:
                    image_storage = BytesIO(f.read())
                reply = Reply(ReplyType.IMAGE, image_storage)
            else:
                reply = Reply(ReplyType.ERROR, "生成图片失败")
                
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            
        except Exception as e:
            logger.error(f"[Glif_Nezha] 发生错误: {e}")
            reply = Reply(ReplyType.ERROR, f"发生错误: {str(e)}")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def generate_image(self, prompt: str, aspect: str, glif_id: str) -> str:
        """调用Glif API生成图片"""
        logger.debug(f"[Glif_Nezha] 生成图片参数: prompt='{prompt}', 比例={aspect}, glif_id={glif_id}")
        
        url = "https://simple-api.glif.app"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "id": glif_id,
            "inputs": [prompt, aspect]
        }
        
        try:
            logger.debug(f"[Glif_Nezha] 发送API请求: {json.dumps(data, ensure_ascii=False)}")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise Exception(result['error'])
            
            logger.debug(f"[Glif_Nezha] API响应成功")
            return result['output']
            
        except Exception as e:
            logger.error(f"[Glif_Nezha] API请求失败: {e}")
            raise

    def extract_aspect_ratio(self, prompt: str) -> str:
        """从提示词中提取宽高比"""
        match = re.search(r'--ar (\d+:\d+)', prompt)
        ratio = match.group(1) if match else "1:1"
        logger.debug(f"[Glif_Nezha] 提取的比例: {ratio}")
        return ratio

    def clean_prompt_string(self, prompt: str) -> str:
        """清理提示词中的参数标记"""
        prompt = re.sub(r'--ar \d+:\d+', '', prompt)
        return prompt.strip()

    def get_help_text(self, **kwargs):
        help_text = "Glif_Nezha文生图插件使用指南：\n"
        help_text += "1. 支持的触发词：\n"
        help_text += "   哪吒、魔丸哪吒|灵珠、灵珠哪吒|成年哪吒|太乙真人|申公豹|敖丙|敖光|敖闰\n"
        help_text += "2. 图片比例说明：\n"
        help_text += "   使用 '--ar' 指定图片比例(1:1、16:9、9:16、4:3、3:4，默认为1:1)\n"
        help_text += "3. 示例：\n"
        help_text += "   魔丸哪吒包饺子 \n"
        help_text += "   灵珠哪吒吃汤圆 --ar 9:16\n"
        help_text += "   成年哪吒喝咖啡 --ar 3:4\n"
        return help_text
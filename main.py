import json
from fastapi import APIRouter, Request
from astrbot.api.all import *

router = APIRouter()

@register("gtmc_feature_webhook", "YourName", "GTMC Webhook 监听插件", "1.0.0")
class GTMCWebhookPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 将路由挂载到 AstrBot 的 FastAPI 服务器上
        self.context.get_server().app.include_router(router)

    @router.post("/webhook/gtmc")
    async def handle_webhook(self, request: Request):
        try:
            payload = await request.json()
        except:
            return {"status": "error", "msg": "Invalid JSON"}
        
        if payload.get("type") == "new_feature":
            data = payload.get("data", {})
            msg = (
                f"🚨 收到新的待解决 Feature！\n"
                f"标题：{data.get('title')}\n"
                f"提交者：{data.get('author')}\n"
                f"标签：{', '.join(data.get('tags', []))}\n"
                f"链接：{data.get('url')}"
            )
            
            # --- 配置你的 QQ 群 ---
            target_group_id = "123456789" # 替换为你的目标QQ群号(字符串格式)
            
            # 遍历当前已连接的平台端发送消息
            for client in self.context.get_server().get_clients():
                # 假设你通过 NapCatQQ 接入，通常会有一个 qq 相关的 client
                try:
                    await client.send_group_message(target_group_id, MessageChain().message(msg))
                except Exception as e:
                    pass # 如果报错可能是个没有加群的bot，忽略继续
                    
        return {"status": "success"}
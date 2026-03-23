import asyncio
import uvicorn
from fastapi import FastAPI, Request
from astrbot.api.all import Star, Context, register, MessageChain
from astrbot.api.message_components import Plain
from astrbot.core.platform.message_session import MessageSession
from astrbot.core.platform.message_type import MessageType

# 开启一个独立的 FastAPI 实例
app = FastAPI()

@register("gtmc_feature_webhook", "YourName", "GTMC Webhook 监听插件", "1.0.0")
class GTMCWebhookPlugin(Star):
    def __init__(self, context: Context, config=None) -> None:
        super().__init__(context)
        self.ctx = context
        self.config = config or {}
        # 将插件实例挂载到 app，以便 FastAPI 路由使用
        app.state.plugin = self 
        
        # 使用 asyncio 在后台启动独立的 webhook 服务器，完全不干扰主程序
        asyncio.create_task(self.start_server())

    async def start_server(self):
        webhook_host = self.config.get("webhook_host", "0.0.0.0")
        webhook_port = int(self.config.get("webhook_port", 8123))
        # 监听独立的 8123 端口，这专门用于你的前后端分离项目
        config = uvicorn.Config(app, host=webhook_host, port=webhook_port, log_level="warning")
        server = uvicorn.Server(config)
        await server.serve()

    async def send_to_qq(self, msg: str):
        target_group = str(self.config.get("target_group", "")).strip()
        platform_name = str(self.config.get("platform_name", "")).strip()
        if not target_group or not platform_name:
            return
        await self.ctx.send_message(
            session=MessageSession(platform_name, MessageType.GROUP_MESSAGE, target_group), 
            message_chain=MessageChain([Plain(msg)])
        )


@app.post("/webhook/gtmc")
async def handle_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
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
        
        # 拿到刚才保存的插件对象进行发送
        plugin: GTMCWebhookPlugin = request.app.state.plugin
        await plugin.send_to_qq(msg)
        
    return {"status": "success"}

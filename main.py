import asyncio
import traceback
import uvicorn
from fastapi import FastAPI, Request
from astrbot.api.all import *

# 开启一个独立的 FastAPI 实例
app = FastAPI()

@register("gtmc_feature_webhook", "YourName", "GTMC Webhook 监听插件", "1.0.0")
class GTMCWebhookPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.ctx = context
        # 将插件实例挂载到 app，以便 FastAPI 路由使用
        app.state.plugin = self 
        
        # 使用 asyncio 在后台启动独立的 webhook 服务器，完全不干扰主程序
        asyncio.create_task(self.start_server())

    async def start_server(self):
        # 监听独立的 8123 端口，这专门用于你的前后端分离项目
        config = uvicorn.Config(app, host="0.0.0.0", port=8123, log_level="warning")
        server = uvicorn.Server(config)
        await server.serve()

    async def send_to_qq(self, msg: str):
        # 🔴 此处修改为你的目标 QQ 群号
        target_group_id = "123456789" 
        
        try:
            # 遍历 AstrBot 已经连接的所有平台实例主动推消息 (兼容最新版本)
            for adapter_id, bot_provider in self.ctx.bots.items():
                if hasattr(bot_provider, "send_group_message"):
                    from astrbot.api.message_components import Plain
                    await bot_provider.send_group_message(target_group_id, [Plain(msg)])
                elif hasattr(bot_provider, "api") and hasattr(bot_provider.api, "send_group_msg"):
                    # 兼容 OneBot11 的原生调用
                    await bot_provider.api.send_group_msg(group_id=int(target_group_id), message=msg)
                    
            self.context.logger.info("[GTMC Webhook] 成功向 QQ 群派发通知")
        except Exception as e:
            self.context.logger.error(f"[GTMC Webhook] 推送消息出错: {e}\n{traceback.format_exc()}")


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
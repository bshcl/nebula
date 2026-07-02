"""Nebula API main entrypoint."""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat
from app.models.db_models import init_db
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.core import mcp_manager  # 👈 导入保险箱

load_dotenv()


# 检查 Key 是否真的加载进来了
MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not MAPS_KEY:
    print("❌ [Nebula] 警告：未在 .env 中找到 GOOGLE_MAPS_API_KEY！")

# 全局变量，用于存放 MCP 会话和动态生成的工具
mcp_session = None
real_world_tools = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 获取 Key
    MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    # 2. 配置参数
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-google-maps"],
        env={**os.environ, "GOOGLE_MAPS_API_KEY": MAPS_KEY},
    )

    print("🌐 [Nebula] 正在启动 Google Maps MCP 服务器...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 3. 初始化握手
                await session.initialize()

                # 4. 💡 核心：只存入保险箱，不抓取工具
                mcp_manager.mcp_session = session
                print("✅ [Nebula] MCP 会话已存入保险箱")

                # 5. 唤醒 World Agent (它会自动去 tools.py 拿你写好的手动工具)
                from app.chains.agents import initialize_world_agent

                initialize_world_agent()

                yield
    except Exception as e:
        print(f"❌ [Nebula] MCP 启动失败: {e}")


app = FastAPI(title="Nebula API", lifespan=lifespan)

init_db()  # 初始化数据库，创建表结构

# 注册路由
# 包含我们后续要写的聊天路由
app.include_router(chat.router, prefix="/api/v1")
# 必须配置 CORS，否则 Next.js 连不上
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Nebula API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

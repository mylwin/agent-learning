from typing import cast

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

# 加载环境变量
load_dotenv()

import os

# 模型配置信息
BASE_URL = os.getenv("LLM_BASE_URL")
API_KEY = os.getenv("LLM_API_KEY")
MODEL_ID = os.getenv("LLM_MODEL_ID")
TIME_OUT = os.getenv("LLM_TIME_OUT")


# 初始化模型
model = init_chat_model(
    model=MODEL_ID,
    model_provider="openai",
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=TIME_OUT,
)

# print(type(model))

# 调用 invoke 方法
# response = model.invoke("月亮的首都是哪里？")
# print(response)

# 调用 stream 方法
# stream_response = model.stream("月亮的首都是哪里？")
# for chunk in stream_response:
#     print(chunk, end="", flush=True)

# init_chat_model() 可能返回 _ConfigurableModel；它在运行时实际是 BaseChatModel，
# 这里用 cast 让类型检查器接受该调用。
agent = create_agent(model=cast(BaseChatModel, model))

# 阻塞调用
# response = agent.invoke(
#     {"messages": [{"role": "user", "content": "月亮的首都是哪里？"}]}
# )

# print(response)


# 创建一个流式调用
for token, metadata in agent.stream(
    {"messages": [{"role": "user", "content": "月亮的首都是哪里？"}]},
    stream_mode="messages",
):
    content = getattr(token, "content", token)
    if content:
        print(content, end="", flush=True)

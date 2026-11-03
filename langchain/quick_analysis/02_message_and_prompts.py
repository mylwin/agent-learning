from typing import cast

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.messages import AIMessage, HumanMessage
from pydantic import BaseModel

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

# 创建一个 Agent
agent = create_agent(model=cast(BaseChatModel, model))
response = agent.invoke(
    {
        "messages": [
            HumanMessage(content="你好我是老八"),
            AIMessage(content="你好老八"),
            HumanMessage(content="我的名字是什么"),
        ]
    }
)
# for message in response["messages"]:
#     message.pretty_print()


agent2 = create_agent(
    model=cast(BaseChatModel, model), system_prompt="像海绵宝宝一样说话。"
)
# for token, metadata in agent2.stream(
#     {"messages": [HumanMessage(content="你是谁？")]}, stream_mode="messages"
# ):
#     content = getattr(token, "content", token)
#     if content:
#         print(content, end="", flush=True)


class CapitalInfo(BaseModel):
    name: str
    location: str
    vibe: str
    economy: str
    population: int


agent3 = create_agent(
    model=cast(BaseChatModel, model),
    system_prompt="你是一位科幻小说作家，根据用户的要求，生成一个太空城市的详细信息。",
    response_format=CapitalInfo,
)

response = agent3.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "火星的最大城市是什么？",
            }
        ]
    }
)
print(response["structured_response"])

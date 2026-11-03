from typing import cast
from unittest import result

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.messages import HumanMessage
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field

# 加载环境变量
load_dotenv()

import os

from langchain.tools import tool

# 模型配置信息
BASE_URL = os.getenv("LLM_BASE_URL")
API_KEY = os.getenv("LLM_API_KEY")
MODEL_ID = os.getenv("LLM_MODEL_ID")
TIME_OUT = os.getenv("LLM_TIME_OUT")


# 使用tool装饰器定义工具
@tool
def get_weather(location: str) -> str:
    """
    Get the weather in a given location.
    Args:
        location: city name or coordinates
    """
    return f"Current weather in {location} is sunny"


# 初始化模型
model = init_chat_model(
    model=MODEL_ID,
    model_provider="openai",
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=TIME_OUT,
)

# 创建一个 Agent
agent = create_agent(
    model=cast(BaseChatModel, model),
    tools=[get_weather],
    system_prompt="你是一个天气助手，可以查询城市天气。",
)
# response = agent.invoke(
#     {"messages": [HumanMessage(content="杭州今天天气如何?")]},
# )

# for message in response["messages"]:
#     message.pretty_print()


# 使用 tavily
tavily = TavilySearch(max_results=3, topic="general")


@tool
def web_search(query: str) -> str:
    """
    联网搜索工具

    Args:
        query: 搜索查询词

    Returns:
        搜索结果摘要
    """
    print(f"▸ 执行搜索: {query}")

    # 尝试使用 Tavily（推荐）
    return tavily.run(query)


# Agent回答内容引用的网页信息
class Reference(BaseModel):
    title: str = Field(description="The title of the web page cited in the answer")
    url: str = Field(description="The url of the web page cited in the answer")


# Agent的回答内容
class AnswerInfo(BaseModel):
    answer: str = Field(description="The final answer for user")
    reference: list[Reference] = Field(description="The web pages cited in the answer")


# 创建智能体，使用预定义工具tavily
agent = create_agent(
    model=cast(BaseChatModel, model),
    tools=[web_search],
    system_prompt="你是一个智能助手，你使用工具来解决用户问题。",
    response_format=AnswerInfo,
)

# 调用agent
response = agent.invoke(
    {"messages": [HumanMessage(content="蒸蚌是什么梗？")]},
)

# 获取结构化输出
if response.get("structured_response"):
    result = response["structured_response"]
    print(f"回答: {result.answer}")
    print("引用网页:")
    for ref in result.reference:
        print(f"- {ref.title}: {ref.url}")

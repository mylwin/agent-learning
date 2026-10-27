from dotenv import load_dotenv
from tavily import TavilyClient

# 加载 .env 文件中的环境变量
load_dotenv()

import os
from collections.abc import Callable
from typing import Any

from serpapi.core import Client


def serp_api_search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误：SERPAPI_API_KEY 未在 .env 文件中配置。"

        params = {
            "engine": "google",
            "q": query,
            "gl": "cn",  # 国家代码
            "hl": "zhs-cn",  # 语言代码
        }

        client = Client(api_key=api_key)
        results = client.search(params)

        # 智能解析：优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if results.get("organic_results"):
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"


def tavily_search(query: str) -> str:
    """
    一个基于Tavily的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    返回前 3 条结果。
    """
    print(f"🔍 正在执行 [Tavily] 网页搜索: {query}")
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "错误：TAVILY_API_KEY 未在 .env 文件中配置。"

        # 创建客户端
        client = TavilyClient(api_key=api_key)

        response = client.search(query=query, max_results=3, search_depth="basic")

        results = response.get("results", [])

        if not results:
            return f"没有找到与 '{query}' 相关的网页结果。"

        return "\n\n".join(
            f"[{i + 1}] {item.get('title', '')}\n"
            f"{item.get('content', '')}\n"
            f"来源：{item.get('url', '')}"
            for i, item in enumerate(results)
        )

    except Exception as e:
        return f"搜索时发生错误: {e}"


class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。
    """

    def __init__(self):
        self.tools: dict[str, dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: Callable[..., Any]):
        """
        向工具箱中注册一个新工具。
        """
        if name in self.tools:
            print(f"警告：工具 '{name}' 已存在，将被覆盖。")

        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> Callable[..., Any] | None:
        """
        根据名称获取一个工具的执行函数。
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join(
            [f"- {name}: {info['description']}" for name, info in self.tools.items()]
        )


# --- 工具初始化与使用示例 1：使用 SerpApi 的工具 ---
# def example_1():
#     # 1. 初始化工具执行器
#     toolExecutor = ToolExecutor()

#     # 2. 注册我们的实战搜索工具
#     search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
#     toolExecutor.registerTool("SerpAPISearch", search_description, serp_api_search)

#     # 3. 打印可用的工具
#     print("\n--- 可用的工具 ---")
#     print(toolExecutor.getAvailableTools())

#     # 4. 智能体的Action调用，这次我们问一个实时性的问题
#     print("\n--- 执行 Action: Search['英伟达最新的GPU型号是什么'] ---")
#     tool_name = "SerpAPISearch"
#     tool_input = "英伟达最新的GPU型号是什么"

#     tool_function = toolExecutor.getTool(tool_name)
#     if tool_function:
#         observation = tool_function(tool_input)
#         print("--- 观察 (Observation) ---")
#         print(observation)
#     else:
#         print(f"错误：未找到名为 '{tool_name}' 的工具。")


# --- 工具初始化与使用示例 2：使用 Tavily 的工具 ---
def example_2():
    # 1. 创建工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册我们的实战搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("TavilySearch", search_description, tavily_search)

    # 3. 获取可用的工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())

    # 4. 智能体的Action调用，这次我们问一个实时性的问题
    print("\n--- 执行 Action: TavilySearch['英伟达最新的GPU型号是什么'] ---")
    tool_name = "TavilySearch"
    tool_input = "英伟达最新的GPU型号是什么"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误：未找到名为 '{tool_name}' 的工具。")


if __name__ == "__main__":
    # example_1()
    example_2()

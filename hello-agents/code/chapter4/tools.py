from dotenv import load_dotenv
from tavily import TavilyClient

# 加载 .env 文件中的环境变量
load_dotenv()

import ast
import operator
import os
from collections.abc import Callable
from typing import Any

from serpapi.core import Client

# 允许的二元/一元运算，用白名单代替 eval，避免执行任意代码
_BINOPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
# 模型常输出的全角符号，统一转成 ASCII 再解析
_FULLWIDTH = str.maketrans(
    {
        "（": "(",
        "）": ")",
        "＋": "+",
        "－": "-",
        "×": "*",
        "÷": "/",
        "＝": "=",
        "　": " ",
    }
)


def _eval_arithmetic(node: ast.AST) -> int | float:
    """递归求值算术表达式 AST，只放行数字、四则运算、整除、取模、乘方与正负号。"""
    # 如果是表达式节点，继续解析其 body
    if isinstance(node, ast.Expression):
        return _eval_arithmetic(node.body)

    # 如果是数字节点，返回值
    if isinstance(node, ast.Constant):
        value = node.value
        # 如果不是数字，则抛出异常
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"不支持的字面量: {value!r}")
        return value

    # 如果是二元/一元运算符，递归解析左右 operand
    if isinstance(node, ast.BinOp):
        func = _BINOPS.get(type(node.op))
        if func is None:
            raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
        left = _eval_arithmetic(node.left)
        right = _eval_arithmetic(node.right)
        # 对于乘方运算，限制指数的绝对值不超过 1000，避免计算过大导致性能问题
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("指数过大，请拆分计算")
        return func(left, right)

    # 如果是一元运算符，递归解析 operand
    if isinstance(node, ast.UnaryOp):
        func = _UNARYOPS.get(type(node.op))
        if func is None:
            raise ValueError(f"不支持的一元运算符: {type(node.op).__name__}")
        return func(_eval_arithmetic(node.operand))

    raise ValueError(f"不支持的表达式节点: {type(node).__name__}")


def calculator(expression: str) -> str:
    """
    一个只做数值计算的计算器工具。

    支持的写法：整数/小数、+ - * / // % **、括号与正负号；
    兼容全角括号与 × ÷ 等符号，例如 "(123 + 456) * 789 / 12"。
    """
    print(f"🧮 正在执行计算: {expression}")

    normalized = expression.translate(_FULLWIDTH).strip().rstrip("=？? ").strip()
    if not normalized:
        return "计算失败：表达式为空。"
    if len(normalized) > 200:
        return "计算失败：表达式过长（上限 200 个字符）。"

    try:
        result = _eval_arithmetic(ast.parse(normalized, mode="eval"))
    except ZeroDivisionError:
        return "计算失败：除数不能为 0。"
    except (SyntaxError, ValueError, TypeError) as e:
        return f"计算失败：{e}"

    # 整数值的浮点结果去掉多余小数位，避免 0.30000000000000004 这类输出
    if isinstance(result, float):
        if result.is_integer():
            return str(int(result))
        return format(result, ".12g")
    return str(result)


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

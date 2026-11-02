
import sys as _run_sys
from pathlib import Path as _RunPath
_run_sys.path.insert(0, str(_RunPath(__file__).resolve().parents[1]))
from run_paths import result_path, memory_config
from dotenv import load_dotenv

# 加载环境
load_dotenv()

from hello_agents import HelloAgentsLLM, SimpleAgent, ToolRegistry
from hello_agents.tools import MemoryTool

# 创建LLM实例
llm = HelloAgentsLLM()

# 创建记忆工具
memory_tool = MemoryTool(memory_config=memory_config(), user_id="user123")
tool_registry = ToolRegistry()
tool_registry.register_tool(memory_tool)

# 创建具有记忆能力的Agent
agent = SimpleAgent(name="记忆助手", llm=llm, tool_registry=tool_registry)

# 体验记忆功能
print("=== 添加多个记忆 ===")

# 添加第一个记忆
result1 = memory_tool.run(
    {
        "action": "add",
        "content": "用户张三是一名Python开发者，专注于机器学习和数据分析",
        "memory_type": "semantic",
        "importance": 0.8,
    }
)
print(f"记忆1: {result1}")

# 添加第二个记忆
result2 = memory_tool.run(
    {
        "action": "add",
        "content": "李四是前端工程师，擅长React和Vue.js开发",
        "memory_type": "semantic",
        "importance": 0.7,
    }
)
print(f"记忆2: {result2}")

# 添加第三个记忆
result3 = memory_tool.run(
    {
        "action": "add",
        "content": "王五是产品经理，负责用户体验设计和需求分析",
        "memory_type": "semantic",
        "importance": 0.6,
    }
)
print(f"记忆3: {result3}")

print("\n=== 搜索特定记忆 ===")
# 搜索前端相关的记忆
print("🔍 搜索 '前端工程师':")
result = memory_tool.run({"action": "search", "query": "前端工程师", "limit": 3})
print(result)

print("\n=== 记忆摘要 ===")
result = memory_tool.run({"action": "summary"})
print(result)

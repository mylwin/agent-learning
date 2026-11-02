
import sys as _run_sys
from pathlib import Path as _RunPath
_run_sys.path.insert(0, str(_RunPath(__file__).resolve().parents[1]))
from run_paths import result_path, memory_config
from pathlib import Path

from dotenv import load_dotenv

# 框架导入时会缓存数据库配置，必须先加载环境变量。
load_dotenv(Path(__file__).with_name(".env"))

from hello_agents import HelloAgentsLLM, SimpleAgent, ToolRegistry
from hello_agents.tools import MemoryTool, RAGTool

# 创建LLM实例
llm = HelloAgentsLLM()

# 创建工具注册表
tool_registry = ToolRegistry()

# 添加记忆工具
memory_tool = MemoryTool(memory_config=memory_config(), user_id="user123")
tool_registry.register_tool(memory_tool)

# 添加RAG工具
rag_tool = RAGTool(knowledge_base_path=result_path("shared", "knowledge_base"))
tool_registry.register_tool(rag_tool)

# 创建Agent并配置工具
agent = SimpleAgent(
    name="智能助手",
    llm=llm,
    system_prompt="你是一个有记忆和知识检索能力的AI助手",
    tool_registry=tool_registry,
)

# result = memory_tool.run(
#     {
#         "action": "add",
#         "content": "用户叫张三，是一名 Python 开发者。",
#         "memory_type": "episodic",
#         "importance": 0.8,
#     }
# )
# print(result)

# 开始对话
response = agent.run("你还记得我是谁吗？")
print(response)

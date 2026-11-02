
import sys as _run_sys
from pathlib import Path as _RunPath
_run_sys.path.insert(0, str(_RunPath(__file__).resolve().parents[1]))
from run_paths import result_path, memory_config
from dotenv import load_dotenv

load_dotenv()

from hello_agents import HelloAgentsLLM, SimpleAgent, ToolRegistry
from hello_agents.tools import RAGTool

# 创建LLM实例
llm = HelloAgentsLLM()

# 创建RAG工具
rag_tool = RAGTool(
    knowledge_base_path=result_path("shared", "knowledge_base"),
    collection_name="test_collection",
    rag_namespace="test",
)

tool_registry = ToolRegistry()
tool_registry.register_tool(rag_tool)

# 创建具有RAG能力的Agent
agent = SimpleAgent(name="知识助手", llm=llm, tool_registry=tool_registry)

# 体验RAG功能
# 添加第一个知识
result1 = rag_tool.execute(
    "add_text",
    text="Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。Python的设计哲学强调代码的可读性和简洁的语法。",
    document_id="python_intro",
)
print(f"知识1: {result1}")

# 添加第二个知识
result2 = rag_tool.execute(
    "add_text",
    text="机器学习是人工智能的一个分支，通过算法让计算机从数据中学习模式。主要包括监督学习、无监督学习和强化学习三种类型。",
    document_id="ml_basics",
)
print(f"知识2: {result2}")

# 添加第三个知识
result3 = rag_tool.execute(
    "add_text",
    text="RAG（检索增强生成）是一种结合信息检索和文本生成的AI技术。它通过检索相关知识来增强大语言模型的生成能力。",
    document_id="rag_concept",
)
print(f"知识3: {result3}")


print("\n=== 搜索知识 ===")
result = rag_tool.execute(
    "search", query="Python编程语言的历史", limit=3, min_score=0.1
)
print(result)

print("\n=== 知识库统计 ===")
result = rag_tool.execute("stats")
print(result)

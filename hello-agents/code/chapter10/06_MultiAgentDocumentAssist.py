"""
多Agent协作的智能文档助手

使用两个SimpleAgent分工协作：
- Agent1：GitHub搜索专家
- Agent2：文档生成专家
"""

from pathlib import Path as _RunPath
from textwrap import dedent

from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM, SimpleAgent
from hello_agents.tools import MCPTool

CHAPTER_DIR = _RunPath(__file__).resolve().parent

# 加载.env文件中的环境变量
load_dotenv()

print("=" * 70)
print("多Agent协作的智能文档助手")
print("=" * 70)

# ============================================================
# Agent 1: GitHub搜索专家
# ============================================================
print("\n【步骤1】创建GitHub搜索专家...")

github_searcher = SimpleAgent(
    name="GitHub搜索专家",
    llm=HelloAgentsLLM(),
    system_prompt=dedent("""
        你是一个GitHub搜索专家。
        你的任务是搜索GitHub仓库并返回结果。
        请返回清晰、结构化的搜索结果，包括：
        - 仓库名称
        - 简短描述

        保持简洁，不要添加额外的解释。""").strip(),
)

# 添加GitHub工具
github_tool = MCPTool(
    name="gh", server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
)
github_searcher.add_tool(github_tool)

# ============================================================
# Agent 2: 文档生成专家
# ============================================================
print("\n【步骤2】创建文档生成专家...")

document_writer = SimpleAgent(
    name="文档生成专家",
    llm=HelloAgentsLLM(),
    system_prompt=dedent("""
        你是一个文档生成专家。
        你的任务是根据提供的信息生成结构化的Markdown报告。

        报告应该包括：
        - 标题
        - 简介
        - 主要内容（分点列出，包括项目名称、描述等）
        - 总结

        请直接输出完整的Markdown格式报告内容，不要使用工具保存。""").strip(),
)

# 添加文件系统工具
fs_tool = MCPTool(
    name="fs",
    server_command=[
        "npx",
        "-y",
        "@modelcontextprotocol/server-filesystem",
        str(CHAPTER_DIR),
    ],
)
document_writer.add_tool(fs_tool)

# ============================================================
# 执行任务
# ============================================================
print("\n" + "=" * 70)
print("开始执行任务...")
print("=" * 70)

try:
    # 步骤1：GitHub搜索
    print("\n【步骤3】Agent1 搜索GitHub...")
    search_task = "搜索关于'AI agent'的GitHub仓库，返回前5个最相关的结果"

    search_results = github_searcher.run(search_task)

    print("\n搜索结果:")
    print("-" * 70)
    print(search_results)
    print("-" * 70)

    # 步骤2：生成报告
    print("\n【步骤4】Agent2 生成报告...")
    report_task = dedent(f"""
        根据以下GitHub搜索结果，生成一份Markdown格式的研究报告：

        {search_results}

        报告要求：
        1. 标题：# AI Agent框架研究报告
        2. 简介：说明这是关于AI Agent的GitHub项目调研
        3. 主要发现：列出找到的项目及其特点（包括名称、描述等）
        4. 总结：总结这些项目的共同特点

        请直接输出完整的Markdown格式报告。
    """)

    report_content = document_writer.run(report_task)

    print("\n报告内容:")
    print("=" * 70)
    print(report_content)
    print("=" * 70)

    # 步骤3：保存报告
    print("\n【步骤5】保存报告到文件...")
    try:
        report_path = CHAPTER_DIR / "report.md"
        report_path.write_text(report_content, encoding="utf-8")
        print(f"✅ 报告已保存到 {report_path}")

        # 验证保存的文件
        file_size = report_path.stat().st_size
        print(f"✅ 文件大小: {file_size} 字节")
    except Exception as e:
        print(f"❌ 保存失败: {e}")

    print("\n" + "=" * 70)
    print("任务完成！")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback

    traceback.print_exc()

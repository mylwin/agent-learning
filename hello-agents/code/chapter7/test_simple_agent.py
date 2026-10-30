from dotenv import load_dotenv
from hello_agents import CalculatorTool, HelloAgentsLLM, ToolRegistry
from my_simple_agent import MySimpleAgent

# 加载环境变量
load_dotenv()

# 创建一个 LLM——框架自动检测 provider
llm = HelloAgentsLLM()


# 测试 1：基础对话 Agent（无工具）
print("\n=== 测试 1：基础对话 Agent（无工具） ===")
basic_agent = MySimpleAgent(
    name="AI助手",
    llm=llm,
    system_prompt="你是一个助手，请尽可能地回答问题。",
    enable_tool_calling=False,
)

response1 = basic_agent.run("你好，介绍下你自己吧!")
print(f"基础对话 Agent 响应: \n{response1}")


# 测试 2：基础对话 Agent（有工具）
print("\n=== 测试 2：基础对话 Agent（有工具） ===")
tool_registry = ToolRegistry()
calculator = CalculatorTool()
tool_registry.register_tool(calculator)

enhance_agent = MySimpleAgent(
    name="AI助手(增强版)",
    llm=llm,
    system_prompt="你是一个助手，请尽可能地回答问题。并且在需要时调用工具。",
    tool_registry=tool_registry,
    enable_tool_calling=True,
)

response2 = enhance_agent.run("帮我计算一下 12345 * 6789 的结果，并解释一下计算过程。")
print(f"基础对话 Agent（有工具）响应: \n{response2}")


# 测试 3：流式响应
print("\n=== 测试 3：流式响应 ===")
print("流式相应：", end=" ")
for chunk in basic_agent.stream_run("请用一句话描述人工智能的未来发展趋势。"):
    pass


# 测试 4：动态添加工具
print("\n=== 测试 4：动态添加工具 ===")
print(f"添加工具前：{basic_agent.has_tools()}")
basic_agent.add_tool(calculator)
print(f"添加工具后：{basic_agent.has_tools()}")
print(f"可用的工具：{basic_agent.list_tools()}")

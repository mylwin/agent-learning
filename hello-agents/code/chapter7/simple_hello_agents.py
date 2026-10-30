from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM, SimpleAgent

# 加载环境变量
load_dotenv()

# 创建一个LLM——框架自动检测 provider
llm = HelloAgentsLLM()

# 创建一个 simple_agent
simple_agent = SimpleAgent(
    name="AI助手", llm=llm, system_prompt="你是一个助手，请尽可能地回答问题。"
)

# 基础的对话
response = simple_agent.run("你好，介绍下你自己吧!")
print(response)

# 添加工具

# 查看对话历史
print(f"历史消息数量: {len(simple_agent.get_history())}")

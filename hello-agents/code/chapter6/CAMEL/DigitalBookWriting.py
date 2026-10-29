import os

from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.societies import RolePlaying
from camel.types import ModelPlatformType
from camel.utils import print_text_animated
from colorama import Fore
from dotenv import load_dotenv

load_dotenv()
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.environ["LLM_BASE_URL"]
LLM_MODEL = os.environ["LLM_MODEL_ID"]

# 创建模型：走通用 OpenAI 兼容接口，base_url 指向平台地址（如硅基流动）
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
    model_type=LLM_MODEL,
    url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)

# 定义协作任务
task_prompt = """
创作一本关于"拖延症心理学"的短篇电子书，目标读者是对心理学感兴趣的普通大众。
要求：
1. 内容科学严谨，基于实证研究
2. 语言通俗易懂，避免过多专业术语
3. 包含实用的改善建议和案例分析
4. 篇幅控制在8000-10000字
5. 结构清晰，包含引言、核心章节和总结
"""

print(Fore.YELLOW + f"协作任务:\n{task_prompt}\n")

# 初始化角色扮演会话
role_play_session = RolePlaying(
    assistant_role_name="心理学家",
    user_role_name="作家",
    task_prompt=task_prompt,
    model=model,
)

print(Fore.CYAN + f"具体任务描述:\n{role_play_session.task_prompt}\n")

# 开始协作对话
chat_turn_limit, n = 30, 0
# 初始化输入消息
input_msg: BaseMessage | None = role_play_session.init_chat()

while input_msg is not None and n < chat_turn_limit:
    n += 1
    # step 方法驱动一轮完整的对话，AI 用户和 AI 助手各自生成一条消息
    assistant_response, user_response = role_play_session.step(input_msg)
    assistant_msg, user_msg = assistant_response.msg, user_response.msg

    # msg 属性仅在本次回复恰好包含一条消息时才非空
    if assistant_msg is None or user_msg is None:
        print(Fore.RED + "未获取到有效回复,结束协作对话")
        break

    print_text_animated(Fore.BLUE + f"作家:\n\n{user_msg.content}\n")
    print_text_animated(Fore.GREEN + f"心理学家:\n\n{assistant_msg.content}\n")

    # 检查任务完成标志
    if "CAMEL_TASK_DONE" in user_msg.content:
        print(Fore.MAGENTA + "✅ 电子书创作完成！")
        break

    input_msg = assistant_msg

print(Fore.YELLOW + f"总共进行了 {n} 轮协作对话")

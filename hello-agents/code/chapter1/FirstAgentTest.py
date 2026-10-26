import os
import re

import requests

from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# 从脚本所在目录向上查找 .env（即 hello-agents/.env）
load_dotenv()

AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束

请开始吧！
"""


def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    # API端点，我们请求JSON格式的数据
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # 发起网络请求
        response = requests.get(url)
        # 检查响应状态码是否为200 (成功)
        response.raise_for_status()
        # 解析返回的JSON数据
        data = response.json()

        # 提取当前天气状况
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        # 格式化成自然语言返回
        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"

    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """

    # 从环境变量或主程序配置中获取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")  # 推荐方式

    if not api_key:
        return "错误：未配置TAVILY_API_KEY。"

    # 2. 初始化Tavily客户端
    tavily = TavilyClient(api_key=api_key)

    # 3. 构造一个精确的查询
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        # 4. 调用API，include_answer=True会返回一个综合性的回答
        response = tavily.search(query=query, search_depth="basic", include_answer=True)

        # 5. Tavily返回的结果已经非常干净，可以直接使用
        # response['answer'] 是一个基于所有搜索结果的总结性回答
        if response.get("answer"):
            return response["answer"]

        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题 - {e}"


# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"


# --- 1. 配置LLM客户端（从环境变量 / .env 读取）---
REQUIRED_ENV = ["OPENAI_API_KEY", "OPENAI_BASE_URL", "MODEL_NAME", "TAVILY_API_KEY"]
missing_env = [name for name in REQUIRED_ENV if not os.getenv(name)]
if missing_env:
    raise RuntimeError(f"缺少环境变量：{', '.join(missing_env)}，请在 hello-agents/.env 中配置")

API_KEY = os.environ["OPENAI_API_KEY"]
BASE_URL = os.environ["OPENAI_BASE_URL"]
MODEL_ID = os.environ["MODEL_NAME"]

llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)

# --- 2. 初始化 ---
user_prompt = "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"
prompt_history = [f"用户请求: {user_prompt}"]

print(f"用户输入: {user_prompt}\n" + "=" * 40)

# --- 3. 运行主循环 ---
for i in range(5):  # 设置最大循环次数
    print(f"--- 循环 {i + 1} ---\n")

    # 3.1. 构建Prompt
    full_prompt = "\n".join(prompt_history)

    # 3.2. 调用LLM进行思考
    llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
    # 模型可能会输出多余的Thought-Action，需要截断
    # 目标：只保留「第一对 Thought...Action...」，丢掉后面多余的轮次
    # 各部分的写法理由：
    #   .*?         非贪婪 —— 只吃到本轮 Action 结束，若用 .* 会一路吞到文本最后
    #   (?=...)     前瞻（零宽）—— 只停在「下一轮标记」之前，不把这个标记算进匹配内容，
    #               所以 group(1) 天然不含分隔符，不用再手动剥离
    #   \n\s*       下一轮标记前可能有换行 + 缩进/空行，用 \s* 兼容
    #   (?:...)     非捕获组 —— 只是把三个候选词括起来做选择，不需要单独取值
    #   \Z          真正的文本结尾；不用 $，因为 $ 还会匹配「末尾换行符之前」的位置
    #   re.DOTALL   让 . 能匹配换行，否则跨行的 Thought/Action 内容根本匹配不上
    # 例：输入 "Thought: 先查天气\nAction: get_weather(city=\"北京\")\nObservation: ...\nThought: 再查景点\nAction: ..."
    #     截断后只剩 "Thought: 先查天气\nAction: get_weather(city=\"北京\")"
    match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
    if match:
        truncated = match.group(1).strip()
        if truncated != llm_output.strip():
            llm_output = truncated
            print("已截断多余的 Thought-Action 对")
    print(f"模型输出:\n{llm_output}\n")
    prompt_history.append(llm_output)

    # 3.3. 解析并执行行动
    # 取「第一个 Action: 」后面的全部文本：.* 贪心 + re.DOTALL 允许内容跨行；
    # 但 "Action:" 后面这个空格是硬性要求，写成 "Action:" 换行再写调用会匹配失败，走下面的报错分支
    # 例：'Action: get_weather(city="北京")' -> 'get_weather(city="北京")'
    action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
    if not action_match:
        observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)
        continue
    action_str = action_match.group(1).strip()

    if action_str.startswith("Finish"):
        # 方括号在正则里是「字符集」语法，所以必须写成 \[ \]；
        # re.match 本身就锚定开头，无需再写 ^；贪心的 (.*) 会取到最后一个 ]，
        # 因此答案里再出现 ] 也不会被截断
        # 例：'Finish[北京今天晴，推荐故宫]' -> '北京今天晴，推荐故宫'
        final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
        print(f"任务完成，最终答案: {final_answer}")
        break

    # \w+ 取函数名（字母/数字/下划线），\( 转义左括号，否则 ( 会被当成分组起点
    # 例：'get_weather(city="北京")' -> 'get_weather'
    tool_name = re.search(r"(\w+)\(", action_str).group(1)
    # 取第一对括号内的参数文本；没加 re.DOTALL，只适用于「调用写在同一行」，参数换行会匹配不到（返回 None）
    # .* 贪婪到最后一个 )，所以 "city=\"北京(朝阳)\"" 这种值里带括号没问题；
    # 但若调用后面还跟了含括号的说明文字，会被一起吞进来（后面的 kwargs 正则只挑 key="value"，一般不受影响）
    # 例：'get_weather(city="北京")' -> 'city="北京"'
    args_str = re.search(r"\((.*)\)", action_str).group(1)
    # [^"]* 表示「一直取到下一个引号为止」：允许空值 ""，也允许值里带逗号和空格，
    # 且不会因为值里出现 "key=" 这类文本而错位
    # findall 得到 [('city', '北京'), ('weather', '晴')]，dict() 转成 {'city': '北京', 'weather': '晴'}
    # 例：参数 'city="北京", weather="晴"' -> {'city': '北京', 'weather': '晴'}
    kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

    if tool_name in available_tools:
        observation = available_tools[tool_name](**kwargs)
    else:
        observation = f"错误：未定义的工具 '{tool_name}'"

    # 3.4. 记录观察结果
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "=" * 40)
    prompt_history.append(observation_str)

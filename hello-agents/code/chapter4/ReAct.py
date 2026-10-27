import re

from llm_client import HelloAgentsLLM
from openai.types.chat import ChatCompletionMessageParam
from tools import ToolExecutor, tavily_search

REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

每次回复必须包含以下两个字段，字段名必须原样输出，Action: 必须位于新的一行：
Thought: 简要说明当前判断和下一步计划。
Action: 行动指令

每次只能输出一条 Action，格式必须是以下两种之一：
1. 调用工具：Action: 工具名称[搜索内容]
2. 结束并回答：Action: Finish[完整的最终答案]

结束时必须把完整答案写在 Finish 的方括号内，并保留前面的 Action:。
不要单独输出 Finish[...]，不要在 Action 之外另写答案，也不要使用 Markdown 代码块。
如果搜索结果不足以确定具体型号或卖点，请说明不确定，不要猜测。

调用工具的示例：
Thought: 我需要搜索最新信息。
Action: TavilySearch[搜索关键词]

结束的示例：
Thought: 已收集到足够的信息，可以回答。
Action: Finish[这里填写根据搜索结果整理出的完整答案。]

现在，请开始解决以下问题：
Question: {question}
History: {history}
"""


class ReActAgent:
    def __init__(
        self,
        llm_client: HelloAgentsLLM,
        tool_executor: ToolExecutor,
        max_steps: int = 5,
    ):
        """
        ReActAgent类构造函数。

        参数：
        - llm_client: 一个LLM客户端，用于生成回复。
        - tool_executor: 一个工具执行器，用于执行工具。
        - max_steps: 最大步骤数，默认为5。
        """
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        """
        运行ReAct代理。

        参数：
        - question: 用户提出的问题。

        返回：最终答案。
        """
        self.history = []
        current_step = 0

        # 循环执行
        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")

            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc, question=question, history=history_str
            )

            messages: list[ChatCompletionMessageParam] = [
                {"role": "user", "content": prompt}
            ]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print("错误：LLM未能返回有效响应。")
                break

            thought, action = self._parse_output(response_text)
            if thought:
                print(f"🤔 思考: {thought}")
            if not action:
                print("警告：未能解析出有效的Action，流程终止。")
                break

            if action.startswith("Finish"):
                # 如果是Finish指令，提取最终答案并结束
                final_answer = self._parse_action_input(action)
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                self.history.append("Observation: 无效的Action格式，请检查。")
                continue

            print(f"🎬 行动: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            observation = (
                tool_function(tool_input)
                if tool_function
                else f"错误：未找到名为 '{tool_name}' 的工具。"
            )

            print(f"👀 观察: {observation}")
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print("已达到最大步数，流程终止。")
        return None

    def _parse_output(self, text: str):
        """
        解析LLM的输出，返回thought和action。

        参数：
        - text: LLM的输出文本。

        返回：thought和action。
        """
        # Thought: 匹配到 Action: 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """
        解析Action，返回tool_name和tool_input。

        参数：
        - action_text: Action文本。

        返回：tool_name和tool_input。
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    def _parse_action_input(self, action_text: str):
        """
        解析Action文本，提取其中的输入内容。

        参数：
        - action_text: Action文本。

        返回：Action中的输入内容。
        """
        match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
        return match.group(1) if match else ""


if __name__ == "__main__":
    # 创建LLM客户端和工具执行器
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    # 注册工具
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.registerTool("TavilySearch", search_desc, tavily_search)
    # 创建ReAct智能体实例
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    agent.run(question)

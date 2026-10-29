import json
import re
from typing import Any

from llm_client import HelloAgentsLLM
from openai.types.chat import ChatCompletionMessageParam
from tools import ToolExecutor, calculator, tavily_search

# 输出协议改为单个 JSON 对象：字段固定，便于程序解析与校验，
# 也避免模型在 Thought/Action 文本里夹带多余内容导致正则失配。
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

你的每次回复必须是一个合法的 JSON 对象，只包含下面两种形式之一。

调用工具时：
{{
  "thought": "简要说明当前判断和下一步计划",
  "action": {{"type": "tool", "tool": "工具名称", "input": "传给工具的参数"}}
}}

给出最终答案时：
{{
  "thought": "说明为什么现有信息已经足够",
  "action": {{"type": "finish", "answer": "完整的最终答案"}}
}}

格式要求（必须严格遵守）：
1. 只输出 JSON 本身，不要输出 Markdown 代码块、解释文字或任何前后缀；
2. action.type 只能是 "tool" 或 "finish"；
3. 调用工具时 tool 必须是上面列出的工具名称之一，input 必须是非空字符串；
4. 结束回答时把完整答案写在 answer 字段，不要另外输出文字；
5. 如果搜索结果不足以确定具体型号或卖点，请在 answer 中说明不确定，不要猜测。

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
        max_parse_failures: int = 2,
    ):
        """
        ReActAgent类构造函数。

        参数：
        - llm_client: 一个LLM客户端，用于生成回复。
        - tool_executor: 一个工具执行器，用于执行工具。
        - max_steps: 最大步骤数，默认为5。
        - max_parse_failures: 允许的输出解析失败次数，超过后终止。
        """
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.max_parse_failures = max_parse_failures
        self.history: list[str] = []

    def run(self, question: str) -> str | None:
        """
        运行ReAct代理。

        参数：
        - question: 用户提出的问题。

        返回：最终答案。
        """
        self.history = []
        current_step = 0
        parse_failures = 0

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

            parsed = self._parse_response(response_text)
            if parsed is None:
                parse_failures += 1
                self.history.append(
                    "Observation: 上一条回复不是合法 JSON，未执行任何动作。"
                    "请严格按模板只输出 JSON 对象。"
                )
                if parse_failures >= self.max_parse_failures:
                    print("警告：连续无法解析输出，流程终止。")
                    break
                continue

            thought, action = parsed
            print(f"🤔 思考: {thought}")

            invalid_reason = self._validate_action(action)
            if invalid_reason:
                self.history.append(f"Observation: 动作校验失败：{invalid_reason}")
                continue

            if action["type"] == "finish":
                final_answer = action["answer"]
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            tool_name = action["tool"]
            tool_input = action["input"]
            print(f"🎬 行动: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            observation = (
                tool_function(tool_input)
                if tool_function
                else f"错误：未找到名为 '{tool_name}' 的工具。"
            )

            print(f"👀 观察: {observation}")
            # 历史里回放同一套 JSON 协议，便于模型保持格式一致
            self.history.append(json.dumps({"action": action}, ensure_ascii=False))
            self.history.append(f"Observation: {observation}")

        print("已达到最大步数，流程终止。")
        return None

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """容错：模型偶尔仍会用 ```json 包裹输出，这里先剥掉围栏。"""
        stripped = text.strip()
        fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, re.DOTALL)
        return fence.group(1).strip() if fence else stripped

    def _parse_response(self, text: str) -> tuple[str, dict[str, Any]] | None:
        """
        解析LLM的输出，返回 (thought, action)。

        参数：
        - text: LLM的输出文本。

        返回：解析成功返回 (thought, action)，失败返回 None。
        """
        try:
            data = json.loads(self._strip_code_fence(text))
        except json.JSONDecodeError as e:
            print(f"警告：LLM 返回的不是合法 JSON（{e}）。")
            return None

        if not isinstance(data, dict):
            print("警告：LLM 返回的 JSON 顶层不是对象。")
            return None

        thought = data.get("thought")
        action = data.get("action")
        if not isinstance(thought, str):
            print("警告：缺少字符串字段 thought。")
            return None
        if not isinstance(action, dict):
            print("警告：缺少对象字段 action。")
            return None
        return thought, action

    def _validate_action(self, action: dict[str, Any]) -> str | None:
        """
        校验action的字段与取值。

        参数：
        - action: 解析出的action字典。

        返回：校验通过返回 None，否则返回错误说明。
        """
        action_type = action.get("type")

        if action_type == "tool":
            tool_name = action.get("tool")
            tool_input = action.get("input")
            if not isinstance(tool_name, str) or not tool_name:
                return 'action.type 为 "tool" 时必须提供非空字符串字段 tool'
            if self.tool_executor.getTool(tool_name) is None:
                return (
                    f"工具 '{tool_name}' 不存在，可用工具："
                    f"{self.tool_executor.getAvailableTools()}"
                )
            if not isinstance(tool_input, str) or not tool_input.strip():
                return 'action.type 为 "tool" 时必须提供非空字符串字段 input'
            return None

        if action_type == "finish":
            answer = action.get("answer")
            if not isinstance(answer, str) or not answer.strip():
                return 'action.type 为 "finish" 时必须提供非空字符串字段 answer'
            return None

        return 'action.type 只能是 "tool" 或 "finish"'


if __name__ == "__main__":
    # 创建LLM客户端和工具执行器
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    # 注册工具
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.registerTool("TavilySearch", search_desc, tavily_search)

    calc_desc = (
        "一个计算器。当需要精确的数值计算（四则运算、整除、取模、乘方、括号）时使用，"
        "input 必须是纯算术表达式字符串，例如 (123 + 456) * 789 / 12。"
    )
    tool_executor.registerTool("Calculator", calc_desc, calculator)

    # 创建ReAct智能体实例
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    # question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    question = "帮我计算 123 * 78 / 12 + 2 ^ 2 的结果"
    agent.run(question)
    # 想单独验证计算器，可改成纯计算问题：
    # agent.run("计算 (123 + 456) * 789 / 12 的结果")

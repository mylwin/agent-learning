"""习题 2：使用显式阶段控制实现可回退的软件开发流程。"""

import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field


@dataclass
class WorkflowResult:
    """
    保存流程状态、每次审查结论和最新代码。

    ready_for_acceptance 表示审查通过、等待人工验收；
    needs_human_review 表示无法自动继续，需要人工处理。
    """

    status: str
    # 每个结果实例都创建自己的列表，避免多个任务共享审查记录。
    history: list[dict[str, str]] = field(default_factory=list)
    code: str = ""


def parse_review(text: str) -> dict[str, str]:
    """
    把模型返回的 JSON 文本转为字典，并校验路由字段。

    支持纯 JSON 或完整的 Markdown JSON 代码块；不提取混杂在正文中的内容。
    verdict 决定下一阶段，feedback 提供退回时的具体修改意见。
    格式无效时抛出 ValueError，由流程转交人工处理。
    """
    # 模型有时会忽略输出格式要求，给 JSON 加上 Markdown 围栏。
    # 只接受完整的单个代码块，避免误把其他文字当成审查结论。
    text = text.strip()
    fenced = re.fullmatch(r"```(?:json)?[ \t]*\r?\n(.*?)\r?\n```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1)
    try:
        review = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise ValueError("审查结果必须是 JSON 对象") from exc
    if (
        not isinstance(review, dict)
        or review.get("verdict")
        not in {"approve", "requirements_change", "code_change"}
        or not isinstance(review.get("feedback"), str)
    ):
        raise ValueError("审查结果必须包含有效的 verdict 和字符串 feedback")
    if review["verdict"] != "approve" and not review["feedback"].strip():
        raise ValueError("退回时必须提供修改意见")
    return review


async def run_workflow(
    task: str, ask: Callable[[str, str], Awaitable[str]], max_rollbacks: int = 3
) -> WorkflowResult:
    """根据审查结果控制阶段和回退；人工验收由调用方执行。

    ask 是异步回调：接收角色名和提示词，返回该角色的文本。
    Callable[[str, str], Awaitable[str]] 描述其参数与返回类型；
    await 会等待异步调用完成，而不是立即取得结果。
    max_rollbacks 限制退回重做次数，不包括首次工程师实现。
    """
    if max_rollbacks < 0:
        raise ValueError("max_rollbacks 不能为负数")
    result = WorkflowResult(status="running")
    requirements = await ask("ProductManager", f"分析需求并给出验收标准：\n{task}")
    feedback = ""
    rollbacks = 0
    # 每次循环执行一轮“实现 → 审查”；最新代码也传给下一轮工程师。
    while True:
        result.code = await ask(
            "Engineer",
            f"需求：\n{requirements}\n修改意见：\n{feedback}\n上一版代码：\n{result.code}",
        )
        review_text = await ask(
            "CodeReviewer",
            (
                f"需求：\n{requirements}\n代码：\n{result.code}\n"
                '仅返回 JSON 对象：{"verdict":"approve|requirements_change|code_change",'
                '"feedback":"具体意见"}。不要使用 Markdown 代码块。'
                '需求变更用 requirements_change，代码问题用 code_change。'
            ),
        )
        try:
            review = parse_review(review_text)
        except ValueError as exc:
            result.history.append({"verdict": "invalid_review", "feedback": str(exc)})
            result.status = "needs_human_review"
            return result
        result.history.append(review)
        if review["verdict"] == "approve":
            result.status = "ready_for_acceptance"
            return result
        # 已用完退回次数时保留最后一次审查意见，交由人工决定。
        if rollbacks >= max_rollbacks:
            result.status = "needs_human_review"
            return result
        rollbacks += 1
        feedback = review["feedback"]
        if review["verdict"] == "requirements_change":
            requirements = await ask(
                "ProductManager",
                (
                    f"原需求：\n{requirements}\n当前代码：\n{result.code}\n"
                    f"审查意见：\n{feedback}\n请重新审核需求并更新验收标准。"
                ),
            )
        # code_change 不需要重新分析需求，直接进入下一轮工程师实现。


async def main() -> None:
    # 仅运行真实团队时才加载 AutoGen；流程测试可注入假的 ask 回调。
    from autogen_agentchat.messages import TextMessage
    from autogen_core import CancellationToken
    from autogen_software_team import (
        create_code_reviewer,
        create_engineer,
        create_openai_model_client,
        create_product_manager,
    )

    # 复用原案例的模型配置与角色提示词，三个角色共享同一个模型客户端。
    client = create_openai_model_client()
    agents = {
        "ProductManager": create_product_manager(client),
        "Engineer": create_engineer(client),
        "CodeReviewer": create_code_reviewer(client),
    }

    async def ask(role: str, prompt: str) -> str:
        # on_reset 清除该智能体的上下文；CancellationToken 是 AutoGen
        # 用于传递取消信号的对象。此处新建 token，并未主动触发取消。
        # 因为上下文被清除，流程必须在 prompt 中传入本轮所需的信息。
        await agents[role].on_reset(CancellationToken())
        # run 异步执行一次任务，返回包含输入和智能体输出消息的 TaskResult。
        response = await agents[role].run(task=prompt)
        # 这里约定最后一条消息是角色的文本回复；先检查类型再读取 content。
        message = response.messages[-1]
        if not isinstance(message, TextMessage):
            raise TypeError(f"{role} 未返回文本消息")
        text = message.content
        print(f"\n--- {role} ---\n{text}")
        return text

    try:
        task = input("请输入开发需求：").strip()
        if not task:
            raise ValueError("开发需求不能为空")
        result = await run_workflow(task, ask)
        print(
            f"\n流程状态：{result.status}；审查记录：{json.dumps(result.history, ensure_ascii=False)}"
        )
        if result.status == "ready_for_acceptance":
            print("请人工运行代码并按照验收标准验证；审查通过不代表测试通过。")
        else:
            print("请人工检查审查结果及代码。")
    finally:
        # 无论成功或异常，都关闭共享客户端并释放底层连接。
        await client.close()


if __name__ == "__main__":
    # 从普通脚本入口创建事件循环，运行异步 main。
    asyncio.run(main())

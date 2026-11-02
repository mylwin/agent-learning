"""
10.3.3 使用 HelloAgents A2A 工具
（3）创建Agent网络
"""

import json
import socket
import threading
import time

from hello_agents.protocols import A2AClient, A2AServer

# 1. 创建多个Agent服务
researcher = A2AServer(name="researcher", description="研究员")


@researcher.skill("research")
def do_research(text: str) -> str:
    import re

    match = re.search(r"research\s+(.+)", text, re.IGNORECASE)
    topic = match.group(1).strip() if match else text
    return json.dumps(
        {"topic": topic, "findings": f"{topic}的研究结果"}, ensure_ascii=False
    )


writer = A2AServer(name="writer", description="撰写员")


@writer.skill("write")
def write_article(text: str) -> str:
    import re

    match = re.search(r"write\s+(.+)", text, re.IGNORECASE)
    content = match.group(1).strip() if match else text

    # 尝试解析研究数据
    try:
        data = json.loads(content)
        topic = data.get("topic", "未知主题")
        findings = data.get("findings", "无研究结果")
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("无法解析研究结果") from exc

    return f"# {topic}\n\n基于研究：{findings}\n\n文章内容..."


editor = A2AServer(name="editor", description="编辑")


@editor.skill("edit")
def edit_article(text: str) -> str:
    import re

    match = re.search(r"edit\s+(.+)", text, re.IGNORECASE | re.DOTALL)
    article = match.group(1).strip() if match else text

    result = {
        "article": article + "\n\n[已编辑优化]",
        "feedback": "文章质量良好",
        "approved": True,
    }
    return str(result)


# 2. 为示例选择空闲端口，避免与本机已有服务冲突
# 注意：端口在探测和服务绑定之间仍可能被其他进程占用。
def available_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_agents():
    clients = []
    for agent in (researcher, writer, editor):
        port = available_port()
        threading.Thread(
            target=agent.run,
            kwargs={"host": "127.0.0.1", "port": port},
            daemon=True,
        ).start()
        client = A2AClient(f"http://127.0.0.1:{port}")
        # 检查实际服务身份，避免连接到其他进程。
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            info = client.get_info()
            if info.get("name") == agent.name:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"{agent.name} 启动失败或端口被占用：{port}")
        clients.append(client)
    return clients


# 4. 协作流程
def get_result(stage, response):
    if response.get("status") != "success" or "result" not in response:
        raise RuntimeError(f"{stage}失败：{response}")
    return response["result"]


def create_content(
    topic: str,
    researcher_client: A2AClient,
    writer_client: A2AClient,
    editor_client: A2AClient,
):
    # 步骤1：研究
    research = researcher_client.execute_skill("research", f"research {topic}")
    research_data = get_result("研究", research)

    # 步骤2：撰写
    article = writer_client.execute_skill("write", f"write {research_data}")
    article_content = get_result("撰写", article)

    # 步骤3：编辑
    final = editor_client.execute_skill("edit", f"edit {article_content}")
    return get_result("编辑", final)


# 使用
if __name__ == "__main__":
    researcher_client, writer_client, editor_client = start_agents()
    result = create_content(
        "AI在医疗领域的应用", researcher_client, writer_client, editor_client
    )
    print(f"\n最终结果：\n{result}")

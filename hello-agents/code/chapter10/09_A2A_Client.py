"""
10.3.3 使用 HelloAgents A2A 工具
（2）创建A2A Agent客户端
"""

import time

from hello_agents.protocols import A2AClient

# 等待服务器启动
time.sleep(1)

# 创建客户端连接到研究员Agent
client = A2AClient("http://127.0.0.1:5000")

# 发送研究请求
response = client.execute_skill("research", "research AI在医疗领域的应用")
if response.get("status") == "error":
    print(f"❌ 请求失败：{response.get('error', response)}")
else:
    print(f"收到响应：{response.get('result')}")

# 输出：
# 收到响应：{'topic': 'AI在医疗领域的应用', 'findings': '关于AI在医疗领域的应用的研究结果...', 'sources': ['来源1', '来源2', '来源3']}

# AgentScope 三国狼人杀案例

本目录包含第六章 AgentScope 框架的完整实战案例，展示了如何使用 AgentScope 构建一个融合中国古典文化元素的多智能体在线游戏。

## 📁 文件说明

- `main_cn.py` - 主要游戏逻辑和控制器
- `prompt_cn.py` - 中文提示词管理
- `game_roles.py` - 游戏角色定义和配置
- `structured_output_cn.py` - 结构化输出模型定义
- `utils_cn.py` - 游戏工具函数和辅助方法
- `README.md` - 本说明文档

## 🎮 案例特点

- **消息驱动架构**：展示 AgentScope 的核心消息传递机制
- **并发协作**：演示多智能体同时在线的实时交互
- **角色扮演**：每个智能体具备双重身份（游戏角色+三国人物）
- **结构化输出**：通过 Pydantic 模型约束智能体行为
- **投票容错**：缺失的投票结果按弃票处理

## 🛠️ 环境准备

### 1. 安装依赖

本示例使用项目根目录的 Python 环境和 AgentScope 2.x（已验证的版本为 2.0.11）。在项目根目录安装依赖并让编辑器选择根目录的 `.venv`：

```bash
uv sync
```

如需单独安装本示例的依赖，可使用 `pip install -r hello-agents/code/chapter6/AgentScopeDemo/requirements.txt`。

### 2. 配置环境变量

本示例使用 OpenAI 兼容的 Chat Completions 接口，与 AutoGen 示例共用以下变量。在项目根目录创建 `.env`，或者在运行前设置环境变量：

```dotenv
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_ID=gpt-4o
```

将地址、模型名和密钥替换为服务商提供的配置；省略 `LLM_BASE_URL` 时使用 OpenAI 默认地址，省略 `LLM_MODEL_ID` 时使用 `gpt-4o`。模型需支持工具调用，AgentScope 使用工具调用生成游戏中的结构化结果。请勿将真实密钥提交到版本控制。

### 3. 运行游戏

```bash
.venv/bin/python hello-agents/code/chapter6/AgentScopeDemo/main_cn.py
```

## 🎭 游戏角色说明

### 游戏角色
- **狼人**：夜晚击杀好人，白天隐藏身份
- **预言家**：每晚查验一名玩家身份
- **女巫**：拥有解药和毒药各一瓶
- **猎人**：被投票出局时可开枪带走一名玩家
- **村民**：通过推理和投票找出狼人

### 三国人物
- **刘备**：仁德宽厚，善于团结众人
- **关羽**：忠义刚烈，言辞直接
- **张飞**：性格豪爽，容易冲动
- **诸葛亮**：智慧超群，分析透彻
- **曹操**：雄才大略，善于权谋
- **司马懿**：深谋远虑，城府极深

## 🏗️ 架构设计

### 分层架构
```
游戏控制层 (ThreeKingdomsWerewolfGame)
    ├── 游戏状态管理
    ├── 流程控制
    └── 胜负判定

智能体交互层 (Agent.observe / Agent.reply)
    ├── 消息路由
    ├── 并发处理
    └── 状态同步

角色建模层 (Agent)
    ├── 角色提示词
    ├── 结构化输出
    └── 行为约束
```

### 核心组件

**1. 消息广播**

讨论按顺序进行，发言通过 `Agent.observe` 发送给其他参与者。

```python
message = await player.reply()
broadcast = UserMsg(name=player.name, content=message.get_text_content() or "")
await asyncio.gather(*(other.observe(broadcast) for other in players if other is not player))
```

**2. 结构化输出和并发投票**

通过 `structured_schema` 指定 Pydantic 模型，并从返回消息的 `structured_output` 读取结果。

```python
vote_msgs = await asyncio.gather(*(
    player.reply(vote_announcement, structured_schema=get_vote_model_cn(players))
    for player in players
))
```

## 🎯 游戏流程

终端展示公开讨论、投票理由以及标记为私有的狼人和角色行动；这些私有信息不会广播给其他阵营。模型内部思考不保证可用。

本示例中，行动目标必须存活，狼人只能选择非狼人，预言家、猎人和白天投票不能选择自己。女巫可以毒杀当晚被狼人选中的玩家；两种死亡原因指向同一玩家时只计算一次。目标无效时重试一次，仍无效则跳过，毒药不会因此消耗。狼人或白天投票平票、无有效票时，无人出局。

### 夜晚阶段
1. **狼人讨论**：狼人通过消息广播协商击杀目标
2. **预言家查验**：预言家选择查验对象
3. **女巫行动**：女巫决定是否使用解药/毒药

### 白天阶段
1. **死亡公布**：公布夜晚死亡玩家
2. **自由讨论**：所有存活玩家参与讨论
3. **投票淘汰**：投票选择淘汰对象
4. **猎人技能**：被淘汰的猎人可开枪

## 🔧 自定义配置

### 修改游戏人数
```python
# 在 main_cn.py 中修改
await game.setup_game(player_count=8)  # 请根据角色配置与可用人物调整人数
```

### 添加新角色
```python
# 在 game_roles.py 中添加
ROLES["守护者"] = {
    "description": "守护者",
    "ability": "每晚可以守护一名玩家",
    "team": "好人阵营"
}
```

### 自定义提示词
```python
# 在 prompt_cn.py 中修改
def get_role_prompt(role: str, character: str) -> str:
    # 自定义角色提示词逻辑
    pass
```

## 🐛 常见问题

### Q: 游戏无法启动？
A: 检查以下几点：
- 确认 `LLM_API_KEY`、`LLM_MODEL_ID` 和 `LLM_BASE_URL` 与所用模型服务匹配
- 验证 API Key 是否有效
- 检查网络连接是否正常

### Q: 智能体输出格式错误？
A: 可能原因：
- 模型理解能力限制
- 提示词设计不够清晰
- 结构化输出约束过于复杂

### Q: 游戏流程卡住？
A: 建议：
- 检查 `Agent.observe` 的消息传递
- 检查并发投票的模型请求
- 查看控制台错误日志

## 📚 技术亮点

### 1. 消息驱动架构
- 智能体间完全通过消息交互
- 支持异步并发处理

### 2. 结构化输出约束
- 游戏规则转化为代码约束
- 提升系统稳定性和可预测性
- 便于调试和监控

### 3. 双重角色建模
- 游戏角色 + 三国人物的创新设计
- 展现不同人格的策略差异
- 增强游戏的趣味性和真实感

## 🚀 扩展方向

- **增加游戏模式**：支持更多狼人杀变体
- **优化 AI 策略**：提升智能体的游戏水平
- **可视化界面**：开发 Web 或桌面客户端
- **实时观战**：支持人类玩家观战和互动
- **数据分析**：统计游戏数据和智能体表现

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request：
- 报告游戏 Bug 或异常
- 提出新功能建议
- 优化代码实现
- 完善文档说明

---

*本案例是 Hello-Agents 教程第六章的核心实战项目，展示了 AgentScope 框架在构建复杂多智能体应用方面的强大能力。*

# Chapter 9 - 上下文工程示例代码

本目录包含第九章"上下文工程"的所有示例代码和演示文件。

## 📁 目录结构

```
chapter9/
├── 01_context_builder_basic.py          # ContextBuilder 基础用法
├── 02_context_builder_with_agent.py     # ContextBuilder 与 Agent 集成
├── 03_note_tool_operations.py           # NoteTool 基本操作
├── 04_note_tool_integration.py          # NoteTool 高级集成
├── 05_terminal_tool_examples.py         # TerminalTool 使用示例
├── 06_three_day_workflow.py             # 完整三天工作流演示
├── codebase_maintainer.py               # 代码库维护助手（核心组件）
├── codebase/                            # 示例代码库
│   ├── data_processor.py
│   ├── api_client.py
│   ├── utils.py
│   └── models.py
├── data/                                # 示例数据
│   └── sales_2024.csv
├── logs/                                # 示例日志
│   └── app.log
└── project/                             # 示例项目
    ├── README.md
    └── main.py
```

## 🚀 快速开始

### 1. 配置嵌入模型

所有使用记忆功能的示例都需要配置嵌入模型。最简单的方式：

```python
import os
# 使用 TF-IDF（无需额外依赖或下载）
os.environ['EMBED_MODEL_TYPE'] = 'tfidf'
os.environ['EMBED_MODEL_NAME'] = ''  # 必须清空
```

### 2. 运行示例

```bash
# 进入 chapter9 目录
cd code/chapter9

# 运行 TerminalTool 示例（无需 LLM）
python 05_terminal_tool_examples.py

# 运行 NoteTool 基本操作（无需 LLM）
python 03_note_tool_operations.py

# 运行完整工作流演示（需要配置 LLM）
python 06_three_day_workflow.py
```

### 3. Windows 中文环境（重要）

`TerminalTool` 内部用 `subprocess` 执行命令，Windows 下默认按系统编码（GBK）解码子进程输出。
当命令输出 UTF-8 中文时会抛 `UnicodeDecodeError`，因为异常发生在读取线程，表现为工具返回空结果，
或者 `❌ 命令执行失败: object of type 'NoneType' has no len()`。

运行前把默认编码切到 UTF-8 即可，不需要改动任何源码：

```bash
# cmd
set PYTHONUTF8=1
python codebase_maintainer.py

# PowerShell
$env:PYTHONUTF8=1
python codebase_maintainer.py

# bash
export PYTHONUTF8=1
python codebase_maintainer.py
```

PyCharm 用户可以在 `Run → Edit Configurations → Environment variables` 中加一行 `PYTHONUTF8=1`。

注意：`dir` 这类 cmd 内建命令仍按 GBK 输出，设了 `PYTHONUTF8=1` 也会失败，建议让 agent 使用
`ls / find / grep / cat / head / tail` 这些命令。

## 📖 示例说明

### 基础示例

#### 01_context_builder_basic.py
- ContextBuilder 的基本用法
- 上下文包（ContextPacket）的创建和管理
- Token 限制和上下文优先级

#### 02_context_builder_with_agent.py
- ContextBuilder 与 SimpleAgent 集成
- 自动上下文管理
- 对话历史的处理

#### 03_note_tool_operations.py
- NoteTool 的 CRUD 操作
- 笔记搜索和标签管理
- 笔记导出功能

#### 04_note_tool_integration.py
- NoteTool 与 ContextBuilder 集成
- 长期项目追踪
- 基于历史笔记的建议

#### 05_terminal_tool_examples.py
- TerminalTool 的典型使用场景
- 探索式导航
- 数据文件分析
- 日志分析
- 代码库分析
- 安全特性演示

### 高级示例

#### 06_three_day_workflow.py
**完整的长程智能体工作流演示**，包括：
- 第一天：探索代码库
- 第二天：分析代码质量
- 第三天：规划重构任务
- 一周后：检查进度
- 跨会话连贯性演示
- 三大工具协同演示

使用我们创建的示例代码库（`./codebase`），包含：
- `data_processor.py` - 数据处理模块（含多个 TODO）
- `api_client.py` - API 客户端（需要改进错误处理）
- `utils.py` - 工具函数（需要优化）
- `models.py` - 数据模型（需要补充验证）

#### codebase_maintainer.py
**核心组件：代码库维护助手**，集成了：
- ContextBuilder - 上下文管理
- NoteTool - 结构化笔记
- TerminalTool - 即时文件访问
- MemoryTool - 对话记忆（仅使用 working 记忆）

## ⚙️ 配置说明

### 嵌入模型配置

有三种选择：

#### 方案一：TF-IDF（推荐用于测试）

```python
import os
os.environ['EMBED_MODEL_TYPE'] = 'tfidf'
os.environ['EMBED_MODEL_NAME'] = ''  # 重要！
```

**优点**：
- ✅ 无需额外依赖
- ✅ 无需 API key
- ✅ 无需下载模型

**缺点**：
- ⚠️ 语义理解能力较弱

#### 方案二：本地 Transformer（推荐用于离线使用）

```python
import os
os.environ['EMBED_MODEL_TYPE'] = 'local'
os.environ['EMBED_MODEL_NAME'] = 'sentence-transformers/all-MiniLM-L6-v2'
os.environ['HF_TOKEN'] = 'your_huggingface_token'
```

**需要**：
1. 安装依赖：`pip install sentence-transformers`
2. Hugging Face Token（从 https://huggingface.co/settings/tokens 获取）
3. 首次运行会下载模型（约 90MB）

**配置 HF Token 的方式**：
```bash
# 方式一：使用 huggingface-cli（推荐，一次配置永久使用）
pip install huggingface-hub
huggingface-cli login

# 方式二：在代码中设置
os.environ['HF_TOKEN'] = 'hf_your_token_here'

# 方式三：命令行设置
export HF_TOKEN="hf_your_token_here"
```

#### 方案三：通义千问 DashScope（推荐用于生产环境）

```python
import os
os.environ['EMBED_MODEL_TYPE'] = 'dashscope'
os.environ['EMBED_MODEL_NAME'] = 'text-embedding-v3'
os.environ['EMBED_API_KEY'] = 'your_dashscope_api_key'
```

**需要**：
1. 注册：https://dashscope.aliyun.com/
2. 获取 API key
3. 安装依赖：`pip install dashscope`

### LLM 配置

如果使用需要 LLM 的示例，需要配置：

```python
from hello_agents import HelloAgentsLLM

# 使用默认配置（需要设置 OPENAI_API_KEY）
llm = HelloAgentsLLM()

# 或者明确指定
llm = HelloAgentsLLM(
    api_key="your_api_key",
    base_url="https://api.openai.com/v1",
    model="gpt-4"
)
```
建议直接在'.env'文件中设置。
    


### 记忆功能配置

`codebase_maintainer.py` 已配置为只使用 `working` 记忆，避免需要 Qdrant 向量数据库：

```python
self.memory_tool = MemoryTool(
    user_id=project_name,
    memory_types=["working"]  # 只使用工作记忆
)
```

如果需要更强大的记忆功能（episodic, semantic），需要安装并启动 Qdrant：

```bash
# 使用 Docker 启动 Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

## 🔍 示例文件说明

### 演示数据文件

#### data/sales_2024.csv
包含 40+ 条销售数据，字段包括：
- date（日期）
- product（产品）
- category（类别：Electronics, Furniture）
- quantity（数量）
- price（价格）
- customer_id（客户ID）
- region（地区：North, South, East, West）

#### logs/app.log
模拟一天的应用日志，包含：
- 多种日志级别（INFO, WARNING, ERROR）
- 多种错误类型（DatabaseConnectionError, ValidationError 等）
- 时间戳从 2024-01-19 14:00 到 23:30

#### codebase/
包含 4 个 Python 模块，共 10+ 个 TODO 注释，适合演示：
- 代码分析
- TODO 查找
- 函数定义搜索
- 代码统计

## 🐛 常见问题

### Q1: RuntimeError: 所有嵌入模型都不可用

**原因**：嵌入模型配置不正确。

**解决**：确保设置了 `EMBED_MODEL_NAME` 为空字符串：

```python
os.environ['EMBED_MODEL_TYPE'] = 'tfidf'
os.environ['EMBED_MODEL_NAME'] = ''  # 必须有这行！
```

### Q2: Qdrant 连接失败

**原因**：默认配置尝试连接 Qdrant 向量数据库。

**解决方案一**（推荐）：使用只需 working 记忆的配置（已在 codebase_maintainer.py 中配置）

**解决方案二**：安装并启动 Qdrant：
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### Q3: 下载 Hugging Face 模型失败

**原因**：网络问题或缺少 Token。

**解决方案**：
1. 配置 HF Token（见上文"方案二"）
2. 或使用镜像：`export HF_ENDPOINT=https://hf-mirror.com`
3. 或改用 TF-IDF：`os.environ['EMBED_MODEL_TYPE'] = 'tfidf'`

### Q4: TerminalTool 提示"不允许的命令"

**原因**：TerminalTool 有白名单限制，只允许安全的命令。

**解决**：使用允许的命令列表中的命令，如：
- 文件操作：ls, cat, head, tail, grep, find
- 文本处理：awk, sed, cut, sort, uniq, wc
- 其他：pwd, cd, tree, stat

## 📝 运行顺序建议

1. **先运行无需 LLM 的示例**：
   - `03_note_tool_operations.py` - 了解 NoteTool
   - `05_terminal_tool_examples.py` - 了解 TerminalTool

2. **配置嵌入模型后运行**：
   - `01_context_builder_basic.py` - 理解上下文管理

3. **配置 LLM 后运行**：
   - `02_context_builder_with_agent.py` - Agent 集成
   - `04_note_tool_integration.py` - 高级集成
   - `06_three_day_workflow.py` - 完整工作流

## 🎯 学习路径

1. **基础概念** → `01_context_builder_basic.py`
2. **工具使用** → `03_note_tool_operations.py`, `05_terminal_tool_examples.py`
3. **Agent 集成** → `02_context_builder_with_agent.py`
4. **高级应用** → `04_note_tool_integration.py`
5. **实战案例** → `06_three_day_workflow.py`

## 💡 提示

- 所有示例都在代码开头包含了嵌入模型配置
- TF-IDF 方案适合快速测试和演示
- 生产环境建议使用 DashScope 或本地 Transformer
- codebase_maintainer.py 是完整的实战案例，值得深入学习

## 📚 相关文档

- 详细文档：`docs/chapter9/第九章 上下文工程.md`
- API 文档：查看各工具类的 docstring
- 项目主页：README.md

## 🤝 贡献

如有问题或建议，欢迎提 Issue 或 PR！


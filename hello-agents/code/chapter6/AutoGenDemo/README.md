# AutoGen 软件开发团队协作案例

本案例使用 AutoGen 的轮流群聊，让产品经理、工程师和代码审查员围绕比特币价格应用协作，并通过用户代理接收人工反馈。

## 文件说明

- `autogen_software_team.py`：创建模型客户端和智能体团队，运行协作对话。
- `output.py`：使用 CoinGecko API 的 Streamlit 比特币价格示例。
- `example_output.py`：另一个价格应用示例，包含缓存和更详细的错误处理。
- `requirements.txt`：本示例所需依赖，与项目根目录的版本要求对齐。

## 环境准备

本案例使用项目根目录的 Python 环境，要求 Python 3.13 或更高版本。当前环境中 AutoGen AgentChat 和 AutoGen Ext 均为 0.7.5。在项目根目录执行：

```bash
uv sync
```

编辑器中请选择项目根目录的 `.venv` 作为 Python 解释器。若需单独安装本案例依赖，可在自己的虚拟环境中执行：

```bash
pip install -r hello-agents/code/chapter6/AutoGenDemo/requirements.txt
```

## 配置模型

脚本使用 `python-dotenv` 加载 `.env`，也可直接设置环境变量。创建项目根目录的 `.env`，根据模型服务填写：

```dotenv
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_ID=gpt-4o
```

`LLM_BASE_URL` 和 `LLM_MODEL_ID` 分别默认为上面的地址和模型名。使用 OpenAI 兼容服务时，请替换为该服务支持的地址、模型和密钥。代码中的 `model_info` 描述模型能力；更换模型时，需根据服务实际支持的功能调整这些配置。不要把真实密钥提交到版本控制。

## 运行团队协作

在项目根目录执行：

```bash
.venv/bin/python hello-agents/code/chapter6/AutoGenDemo/autogen_software_team.py
```

团队按产品经理、工程师、代码审查员、用户代理的顺序轮流对话。`UserProxyAgent` 会等待终端输入；输入反馈可继续对话，输入 `TERMINATE` 可触发结束条件，团队也会在最多 20 轮后结束。用户代理本身不会自动运行或测试生成的代码，需要人工验证结果。

调用模型需要有效的 API 配置和网络连接，可能产生模型服务费用。团队对话生成的代码不会自动写入 `output.py`。

## 运行价格示例

在项目根目录执行：

```bash
.venv/bin/streamlit run hello-agents/code/chapter6/AutoGenDemo/output.py
```

如需运行另一个示例，将命令中的 `output.py` 替换为 `example_output.py`。两个示例均需联网访问 CoinGecko API，数据可用性和请求频率受该服务限制。

## 自定义与排查

- 在 `autogen_software_team.py` 中修改角色提示词、任务、参与者列表或 `max_turns`，调整团队行为。
- 模型调用失败时，检查 API 密钥、服务地址、模型名、模型能力配置和网络连接。
- 对话等待输入时，请在终端提供反馈；输入 `TERMINATE` 可结束对话。
- 价格显示失败时，检查 CoinGecko API 的网络连接和响应状态。

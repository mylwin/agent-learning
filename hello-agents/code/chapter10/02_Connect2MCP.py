import asyncio
from pathlib import Path

from hello_agents.protocols import MCPClient

# 固定 MCP 文件访问目录，不受运行命令时的工作目录影响
CHAPTER_DIR = Path(__file__).resolve().parent


async def connect_to_server():
    # 方式1：连接到社区提供的文件系统服务器
    # npx会自动下载并运行@modelcontextprotocol/server-filesystem包
    client = MCPClient(
        [
            "npx",
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(CHAPTER_DIR),  # 指定允许访问的目录
        ]
    )

    # 使用async with确保连接正确关闭
    async with client:
        # 在这里使用client
        tools = await client.list_tools()
        print(f"可用工具: {[t['name'] for t in tools]}")

    # 方式2：连接到自定义的Python MCP服务器
    client = MCPClient(["python", str(CHAPTER_DIR / "my_mcp_server.py")])
    async with client:
        # 使用client...
        pass


# 可用工具: ['read_file', 'read_text_file', 'read_media_file',
# 'read_multiple_files', 'write_file', 'edit_file', 'create_directory',
# 'list_directory', 'list_directory_with_sizes', 'directory_tree',
# 'move_file', 'search_files', 'get_file_info', 'list_allowed_directories']

# 运行异步函数
# asyncio.run(connect_to_server())


async def discover_tools():
    client = MCPClient(
        ["npx", "-y", "@modelcontextprotocol/server-filesystem", str(CHAPTER_DIR)]
    )

    async with client:
        # 获取所有可用工具
        tools = await client.list_tools()

        print(f"服务器提供了 {len(tools)} 个工具：")
        for tool in tools:
            print(f"\n工具名称: {tool['name']}")
            print(f"描述: {tool.get('description', '无描述')}")

            # 打印参数信息
            if "inputSchema" in tool:
                schema = tool["inputSchema"]
                if "properties" in schema:
                    print("参数:")
                    for param_name, param_info in schema["properties"].items():
                        param_type = param_info.get("type", "any")
                        param_desc = param_info.get("description", "")
                        print(f"  - {param_name} ({param_type}): {param_desc}")


# asyncio.run(discover_tools())

# 输出示例：
# 服务器提供了 5 个工具：
#
# 工具名称: read_file
# 描述: 读取文件内容
# 参数:
#   - path (string): 文件路径
#
# 工具名称: write_file
# 描述: 写入文件内容
# 参数:
#   - path (string): 文件路径
#   - content (string): 文件内容


async def use_tools():
    client = MCPClient(
        ["npx", "-y", "@modelcontextprotocol/server-filesystem", str(CHAPTER_DIR)]
    )

    async with client:
        # 读取文件
        result = await client.call_tool(
            "read_file", {"path": str(CHAPTER_DIR / "my_README.md")}
        )
        print(f"文件内容：\n{result}")

        # 列出目录
        result = await client.call_tool("list_directory", {"path": str(CHAPTER_DIR)})
        print(f"当前目录文件：{result}")

        # 写入文件
        result = await client.call_tool(
            "write_file",
            {"path": str(CHAPTER_DIR / "output.txt"), "content": "Hello from MCP!"},
        )
        print(f"写入结果：{result}")


# asyncio.run(use_tools())


async def safe_tool_call():
    client = MCPClient(
        ["npx", "-y", "@modelcontextprotocol/server-filesystem", str(CHAPTER_DIR)]
    )

    async with client:
        try:
            # 尝试读取可能不存在的文件
            result = await client.call_tool("read_file", {"path": "nonexistent.txt"})
            print(result)
        except Exception as e:
            print(f"工具调用失败: {e}")
            # 可以选择重试、使用默认值或向用户报告错误


asyncio.run(safe_tool_call())

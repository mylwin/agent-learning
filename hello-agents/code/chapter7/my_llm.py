# my_llm.py
import os

from hello_agents import HelloAgentsLLM
from openai import OpenAI


class MyLLM(HelloAgentsLLM):
    """
    自定义 LLM 类，通过继承 HelloAgentsLLM 类实现对 ModelScope Provider 的支持。
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        provider: str | None = "auto",
        **kwargs,
    ):
        # 检查provider是否为我们想处理的'modelscope'
        if provider == "modelscope":
            print("正在使用自定义的 ModelScope Provider")
            self.provider = "modelscope"

            # 解析 ModelScope 的凭证
            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY")
            self.base_url = base_url or "https://api-inference.modelscope.cn/v1"

            # 验证凭证是否存在
            if not self.api_key:
                raise ValueError(
                    "ModelScope API key not found. Please set MODELSCOPE_API_KEY environment variable."
                )

            # 设置默认模型和其他参数
            self.model = model or os.getenv("MODELSCOPE_MODEL_ID") or "Qwen/Qwen3.8-27B"
            self.temperature = kwargs.get("temperature", 0.7)
            self.max_tokens = kwargs.get("max_tokens")
            self.timeout = kwargs.get("timeout", 60)

            # 使用获取的参数创建OpenAI客户端实例
            self._client = OpenAI(
                api_key=self.api_key, base_url=self.base_url, timeout=self.timeout
            )

        else:
            # 如果不是 modelscope, 则完全使用父类的原始逻辑来处理

            super().__init__(
                model=model,
                api_key=api_key,
                base_url=base_url,
                provider=provider,  # type: ignore[arg-type]
                **kwargs,
            )

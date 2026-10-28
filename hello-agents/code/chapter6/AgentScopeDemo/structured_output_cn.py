"""三国狼人杀游戏的结构化输出模型"""

from collections.abc import Sequence
from typing import Literal

from agentscope.agent import Agent
from pydantic import BaseModel, Field, create_model


class DiscussionModelCN(BaseModel):
    """中文版讨论输出格式"""

    reach_agreement: bool = Field(
        description="是否已达成一致意见",
    )
    confidence_level: int = Field(description="对当前推理的信心程度(1-10)", ge=1, le=10)
    key_evidence: str | None = Field(description="支持你观点的关键证据", default=None)


def get_vote_model_cn(agents: Sequence[Agent]) -> type[BaseModel]:
    """获取中文版投票模型"""

    # 1. 提前把姓名提取为元组
    agent_names = tuple(_.name for _ in agents)

    # 2. 使用 create_model 动态构建
    VoteModelCN = create_model(
        "VoteModelCN",
        # 这里的 Literal 会在运行时生效
        vote=(Literal[agent_names], Field(description="你要投票淘汰的玩家姓名")),  # type: ignore
        reason=(str, Field(description="投票理由，简要说明为什么选择此人")),
        suspicion_level=(
            int,
            Field(description="对被投票者的怀疑程度(1-10)", ge=1, le=10),
        ),
    )

    # 3. 补充 Docstring
    VoteModelCN.__doc__ = "中文版投票输出格式"

    return VoteModelCN


class WitchActionModelCN(BaseModel):
    """中文版女巫行动模型"""

    use_antidote: bool = Field(description="是否使用解药救人", default=False)
    use_poison: bool = Field(description="是否使用毒药杀人", default=False)
    target_name: str | None = Field(
        description="目标玩家姓名（救人或毒杀的对象）", default=None
    )
    action_reason: str | None = Field(description="行动理由", default=None)


def get_seer_model_cn(agents: Sequence[Agent]) -> type[BaseModel]:
    """获取中文版预言家模型"""

    # 1. 提前把姓名提取为元组
    agent_names = tuple(_.name for _ in agents)

    # 2. 使用 create_model 动态构建
    SeerModelCN = create_model(
        "SeerModelCN",
        # 这里的 Literal 会在运行时生效
        target=(Literal[agent_names], Field(description="要查验的玩家姓名")),  # type: ignore
    )

    # 3. 补充 Docstring
    SeerModelCN.__doc__ = "中文版预言家查验格式"

    return SeerModelCN


def get_hunter_model_cn(agents: Sequence[Agent]) -> type[BaseModel]:
    """获取中文版猎人模型"""

    # 1. 提前把姓名提取为元组
    agent_names = tuple(_.name for _ in agents)

    # 2. 使用 create_model 动态构建
    HunterModelCN = create_model(
        "HunterModelCN",
        shoot=(bool, Field(description="是否使用开枪技能")),
        target=(Literal[agent_names], Field(description="要开枪的玩家姓名")),  # type: ignore
    )

    # 3. 补充 Docstring
    HunterModelCN.__doc__ = "中文版猎人开枪格式"

    return HunterModelCN


class WerewolfKillModelCN(BaseModel):
    """中文版狼人击杀模型"""

    target: str = Field(
        description="要击杀的玩家姓名",
    )
    kill_strategy: str = Field(
        description="击杀策略说明",
    )
    team_coordination: str | None = Field(
        description="与狼队友的配合计划", default=None
    )


class GameAnalysisModelCN(BaseModel):
    """中文版游戏分析模型"""

    suspected_werewolves: list[str] = Field(
        description="怀疑的狼人名单", default_factory=list
    )
    trusted_players: list[str] = Field(
        description="信任的玩家名单", default_factory=list
    )
    key_clues: list[str] = Field(description="关键线索列表", default_factory=list)
    next_strategy: str = Field(
        description="下一步策略",
    )

"""三国狼人杀游戏工具函数"""

import random
from collections import Counter
from collections.abc import Sequence
from typing import Any

from agentscope.agent import Agent
from agentscope.message import Msg, UserMsg

# 游戏常量
MAX_GAME_ROUND = 10  # 最大游戏轮数
MAX_DISCUSSION_ROUND = 3  # 最大讨论轮数

# 角色名称
CHINESE_NAMES = [
    "刘备",
    "关羽",
    "张飞",
    "诸葛亮",
    "赵云",
    "曹操",
    "司马懿",
    "典韦",
    "许褚",
    "夏侯惇",
    "孙权",
    "周瑜",
    "陆逊",
    "甘宁",
    "太史慈",
    "吕布",
    "貂蝉",
    "董卓",
    "袁绍",
    "袁术",
]


def get_chinese_name(character: str | None = None) -> str:
    """获取中文角色名"""
    if character and character in CHINESE_NAMES:
        return character
    return random.choice(CHINESE_NAMES)


def format_player_list(players: Sequence[Agent], show_roles: bool = False) -> str:
    """格式化玩家列表为中文显示"""
    if not players:
        return "无玩家"

    if show_roles:
        return "、".join([f"{p.name}({getattr(p, 'role', '未知')})" for p in players])
    else:
        return "、".join([p.name for p in players])


def majority_vote_cn(votes: dict[str, str | None]) -> tuple[str, int]:
    """中文版多数投票统计"""
    valid_votes = [vote for vote in votes.values() if vote is not None]
    if not valid_votes:
        return "无人", 0

    vote_counts = Counter(valid_votes)
    most_voted = vote_counts.most_common(1)[0]

    return most_voted[0], most_voted[1]


def check_winning_cn(
    alive_players: Sequence[Agent], roles: dict[str, str]
) -> str | None:
    """检查中文版游戏胜利条件"""
    alive_roles = [roles.get(p.name, "村民") for p in alive_players]
    werewolf_count = alive_roles.count("狼人")
    villager_count = len(alive_roles) - werewolf_count

    if werewolf_count == 0:
        return "好人阵营胜利！所有狼人已被淘汰！"
    elif werewolf_count >= villager_count:
        return "狼人阵营胜利！狼人数量已达到或超过好人！"

    return None


def analyze_speech_pattern(speech: str) -> dict[str, Any]:
    """分析发言模式（中文优化）"""
    analysis = {
        "word_count": len(speech),  # 词数
        "confidence_keywords": 0,  # 确信度
        "doubt_keywords": 0,  # 怀疑度
        "emotion_score": 0,  # 情感分数（正面为正，负面为负）
    }

    # 中文关键词分析
    confidence_words = ["确定", "肯定", "一定", "绝对", "必须", "显然"]
    doubt_words = ["可能", "也许", "或许", "怀疑", "不确定", "感觉"]

    for word in confidence_words:
        analysis["confidence_keywords"] += speech.count(word)

    for word in doubt_words:
        analysis["doubt_keywords"] += speech.count(word)

    # 简单情感分析
    positive_words = ["好", "棒", "赞", "支持", "同意"]
    negative_words = ["坏", "差", "反对", "不行", "错误"]

    for word in positive_words:
        analysis["emotion_score"] += speech.count(word)

    for word in negative_words:
        analysis["emotion_score"] -= speech.count(word)

    return analysis


class GameModerator:
    """中文版游戏主持人"""

    def __init__(self) -> None:
        self.name = "游戏主持人"
        self.game_log: list[str] = []

    async def announce(self, content: str) -> Msg:
        """发布游戏公告"""
        msg = UserMsg(name=self.name, content=f"📢 {content}")
        self.game_log.append(content)
        print(f"📢 {content}")
        return msg

    async def night_announcement(self, round_num: int) -> Msg:
        """夜晚阶段公告"""
        content = f"🌙 第{round_num}夜降临，天黑请闭眼..."
        return await self.announce(content)

    async def day_announcement(self, round_num: int) -> Msg:
        """白天阶段公告"""
        content = f"☀️ 第{round_num}天天亮了，请大家睁眼..."
        return await self.announce(content)

    async def death_announcement(self, dead_players: list[str]) -> Msg:
        """死亡公告"""
        if not dead_players:
            content = "昨夜平安无事，无人死亡。"
        else:
            content = f"昨夜，{format_player_list_str(dead_players)}不幸遇害。"
        return await self.announce(content)

    async def vote_result_announcement(self, voted_out: str, vote_count: int) -> Msg:
        """投票结果公告"""
        content = f"投票结果：{voted_out}以{vote_count}票被淘汰出局。"
        return await self.announce(content)

    async def game_over_announcement(self, winner: str) -> Msg:
        """游戏结束公告"""
        content = f"🎉 游戏结束！{winner}"
        return await self.announce(content)


def format_player_list_str(players: list[str]) -> str:
    """格式化玩家姓名列表"""
    if not players:
        return "无人"
    return "、".join(players)


def calculate_suspicion_score(player_name: str, game_history: list[dict]) -> float:
    """计算玩家可疑度分数"""
    score = 0.0

    for event in game_history:
        # 如果玩家被投票，则可疑度分数加0.3
        if event.get("type") == "vote" and event.get("target") == player_name:
            score += 0.3
        # 如果玩家被指控，则可疑度分数加0.2
        elif event.get("type") == "accusation" and event.get("target") == player_name:
            score += 0.2
        # 如果玩家防守，则可疑度分数减0.1
        elif event.get("type") == "defense" and event.get("player") == player_name:
            score -= 0.1

    return min(max(score, 0.0), 1.0)


async def handle_interrupt(*args: Any, **kwargs: Any) -> Msg:
    """处理游戏中断"""
    return UserMsg(name="系统", content="游戏被中断")

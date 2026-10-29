"""
三国狼人杀 - 基于AgentScope的中文版狼人杀游戏
融合三国演义角色和传统狼人杀玩法
"""

import asyncio
import os
import random

from agentscope.agent import Agent
from agentscope.credential import OpenAICredential
from agentscope.formatter import OpenAIMultiAgentFormatter
from agentscope.message import UserMsg
from agentscope.model import OpenAIChatModel
from dotenv import load_dotenv
from game_roles import GameRoles
from prompt_cn import ChinesePrompts
from pydantic import SecretStr
from structured_output_cn import (
    DiscussionModelCN,
    get_hunter_model_cn,
    get_seer_model_cn,
    get_vote_model_cn,
    get_werewolf_model_cn,
    get_witch_model_cn,
)
from utils_cn import (
    MAX_DISCUSSION_ROUND,
    MAX_GAME_ROUND,
    GameModerator,
    check_winning_cn,
    format_player_list,
    get_chinese_name,
    majority_vote_cn,
)

load_dotenv()


class ThreeKingdomsWerewolfGame:
    """三国狼人杀游戏主类"""

    def __init__(self):
        self.players: dict[str, Agent] = {}
        self.roles: dict[str, str] = {}
        self.moderator = GameModerator()
        self.alive_players: list[Agent] = []
        self.werewolves: list[Agent] = []
        self.villagers: list[Agent] = []
        self.seer: list[Agent] = []
        self.witch: list[Agent] = []
        self.hunter: list[Agent] = []

        # 女巫道具状态
        self.witch_has_antidote = True
        self.witch_has_poison = True

    async def create_player(self, role: str, character: str) -> Agent:
        """创建具有三国背景的玩家"""
        name = get_chinese_name(character)
        self.roles[name] = role

        agent = Agent(
            name=name,
            system_prompt=ChinesePrompts.get_role_prompt(role, character),
            model=OpenAIChatModel(
                model=os.getenv("LLM_MODEL_ID", "gpt-4o"),
                credential=OpenAICredential(
                    api_key=SecretStr(os.environ["LLM_API_KEY"]),
                    base_url=os.getenv("LLM_BASE_URL") or None,
                ),
                formatter=OpenAIMultiAgentFormatter(),
            ),
        )

        # 角色身份确认。observe()接收外部观察消息并将其保存到 上下文。
        await agent.observe(
            await self.moderator.announce(
                f"【{name}】你在这场三国狼人杀中扮演{GameRoles.get_role_desc(role)}，"
                f"你的角色是{character}。{GameRoles.get_role_ability(role)}"
            )
        )

        self.players[name] = agent
        return agent

    async def setup_game(self, player_count: int = 6):
        """设置游戏"""
        print("🎮 开始设置三国狼人杀游戏...")

        # 获取角色配置
        roles = GameRoles.get_standard_setup(player_count)
        # 随机获取 player_count 个角色
        characters = random.sample(
            [
                "刘备",
                "关羽",
                "张飞",
                "诸葛亮",
                "赵云",
                "曹操",
                "司马懿",
                "周瑜",
                "孙权",
            ],
            player_count,
        )

        # 创建玩家
        for role, character in zip(roles, characters):
            agent = await self.create_player(role, character)
            # 将玩家加入存活列表
            self.alive_players.append(agent)

            # 分配到对应阵营
            if role == "狼人":
                self.werewolves.append(agent)
            elif role == "预言家":
                self.seer.append(agent)
            elif role == "女巫":
                self.witch.append(agent)
            elif role == "猎人":
                self.hunter.append(agent)
            else:
                self.villagers.append(agent)

        # 游戏开始公告
        await self.moderator.announce(
            f"三国狼人杀游戏开始！参与者：{format_player_list(self.alive_players)}"
        )

        print(f"✅ 游戏设置完成，共{len(self.alive_players)}名玩家")

    async def public_update(self, text: str):
        """向存活玩家同步公开信息。"""
        message = await self.moderator.announce(text)
        await asyncio.gather(*(p.observe(message) for p in self.alive_players))

    async def choose(self, player, schema, field, candidates, label, enabled=None):
        """校验目标；无效时最多重试一次。"""
        if not candidates:
            print(f"⚠️ {label}没有合法目标，跳过")
            return None, {}
        names = {p.name for p in candidates}
        prompt = f"{label}，合法目标：{'、'.join(sorted(names))}。"
        first_antidote = None
        for attempt in range(2):
            msg = await player.reply(
                UserMsg(name="主持人", content=prompt), structured_schema=schema
            )
            data = msg.structured_output or {}
            if label == "女巫毒杀":
                if first_antidote is None:
                    first_antidote = bool(data.get("use_antidote"))
                data = {**data, "use_antidote": first_antidote}
            if enabled and not data.get(enabled):
                return None, data
            target = data.get(field)
            if isinstance(target, str) and target in names:
                return target, data
            print(
                f"⚠️ {player.name} 的{label}目标无效：{target}（{'重新选择' if attempt == 0 else '跳过'}）"
            )
            prompt = f"目标无效，请重新选择。合法目标：{'、'.join(sorted(names))}。"
        return None, {
            "use_antidote": first_antidote
        } if first_antidote is not None else {}

    async def werewolf_phase(self, round_num: int):
        if not self.werewolves:
            return None
        candidates = [p for p in self.alive_players if p not in self.werewolves]
        if not candidates:
            return None
        announcement = await self.moderator.announce(
            f"🐺 狼人私聊：讨论击杀目标，合法目标：{format_player_list(candidates)}"
        )
        await asyncio.gather(*(wolf.observe(announcement) for wolf in self.werewolves))
        for round_index in range(MAX_DISCUSSION_ROUND):
            for wolf in self.werewolves:
                message = await wolf.reply(structured_schema=DiscussionModelCN)
                data = message.structured_output or {}
                content = (
                    f"建议目标：{data.get('proposed_target', '未指定')}；"
                    f"理由：{data.get('reason', '未提供')}；"
                    f"是否达成一致：{data.get('reach_agreement', '未知')}；"
                    f"证据：{data.get('key_evidence') or '无'}"
                )
                print(f"🐺 [狼人私聊 第{round_index + 1}轮] {wolf.name}：{content}")
                broadcast = UserMsg(name=wolf.name, content=content)
                await asyncio.gather(
                    *(
                        other.observe(broadcast)
                        for other in self.werewolves
                        if other is not wolf
                    )
                )
        choices = await asyncio.gather(
            *(
                self.choose(
                    w,
                    get_werewolf_model_cn(candidates),
                    "target",
                    candidates,
                    "狼人击杀",
                )
                for w in self.werewolves
            )
        )
        votes = {}
        for wolf, (target, data) in zip(self.werewolves, choices):
            votes[wolf.name] = target
            print(
                f"🐺 [狼人投票] {wolf.name} → {target or '弃票'}；理由：{data.get('kill_strategy', '无')}"
            )
        target, count = majority_vote_cn(votes)
        print(f"🐺 [狼人投票结果] {target}（{count}票；平票或无有效票则无人遇袭）")
        return None if target == "无人" else target

    async def seer_phase(self):
        if not self.seer:
            return
        seer = self.seer[0]
        candidates = [p for p in self.alive_players if p is not seer]
        target, _ = (
            await self.choose(
                seer, get_seer_model_cn(candidates), "target", candidates, "预言家查验"
            )
            if candidates
            else (None, {})
        )
        if target:
            result = f"查验结果：{target}是{'狼人' if self.roles[target] == '狼人' else '好人'}"
            await seer.observe(await self.moderator.announce(f"[预言家私有] {result}"))

    async def witch_phase(self, killed_player: str | None):
        if not self.witch:
            return killed_player, None
        witch = self.witch[0]
        candidates = list(self.alive_players)
        info = f"今晚{killed_player}被狼人击杀" if killed_player else "今晚平安无事"
        info += f"；解药{'可用' if self.witch_has_antidote else '已用'}，毒药{'可用' if self.witch_has_poison else '已用'}。可毒杀当晚遇袭玩家。"
        await witch.observe(await self.moderator.announce(f"[女巫私有] {info}"))
        target, action = await self.choose(
            witch,
            get_witch_model_cn(candidates),
            "target_name",
            candidates,
            "女巫毒杀",
            enabled="use_poison",
        )
        saved = bool(
            action.get("use_antidote") and self.witch_has_antidote and killed_player
        )
        if saved:
            self.witch_has_antidote = False
            print(f"🧙 [女巫私有] 使用解药救了{killed_player}")
        if target and self.witch_has_poison:
            self.witch_has_poison = False
            print(
                f"🧙 [女巫私有] 毒杀{target}；理由：{action.get('action_reason') or '无'}"
            )
        else:
            target = None
        return (None if saved else killed_player), target

    async def hunter_phase(self, shot_by_hunter: str | None):
        if not self.hunter or self.hunter[0].name != shot_by_hunter:
            return None
        hunter = self.hunter[0]
        candidates = [p for p in self.alive_players if p.name != shot_by_hunter]
        if not candidates:
            return None
        target, _ = await self.choose(
            hunter,
            get_hunter_model_cn(candidates),
            "target",
            candidates,
            "猎人开枪",
            enabled="shoot",
        )
        if target:
            await self.moderator.announce(f"猎人{hunter.name}开枪带走了{target}")
        return target

    def update_alive_players(self, dead_players: list[str]):
        """更新存活玩家列表"""
        for dead_name in dead_players:
            if dead_name:
                # 从存活列表移除
                self.alive_players = [
                    p for p in self.alive_players if p.name != dead_name
                ]
                # 从各阵营移除
                self.werewolves = [p for p in self.werewolves if p.name != dead_name]
                self.villagers = [p for p in self.villagers if p.name != dead_name]
                self.seer = [p for p in self.seer if p.name != dead_name]
                self.witch = [p for p in self.witch if p.name != dead_name]
                self.hunter = [p for p in self.hunter if p.name != dead_name]

    async def day_phase(self, round_num: int):
        """白天阶段"""
        await self.moderator.day_announcement(round_num)

        announcement = await self.moderator.announce(
            f"现在开始自由讨论。存活玩家：{format_player_list(self.alive_players)}"
        )
        await asyncio.gather(
            *(player.observe(announcement) for player in self.alive_players)
        )
        for player in self.alive_players:
            message = await player.reply()
            content = message.get_text_content() or "（无发言）"
            print(f"💬 [公开讨论] {player.name}：{content}")
            broadcast = UserMsg(name=player.name, content=content)
            await asyncio.gather(
                *(
                    other.observe(broadcast)
                    for other in self.alive_players
                    if other is not player
                )
            )

        async def vote(player):
            candidates = [p for p in self.alive_players if p is not player]
            if not candidates:
                return None, {}
            return await self.choose(
                player, get_vote_model_cn(candidates), "vote", candidates, "白天投票"
            )

        results = await asyncio.gather(*(vote(player) for player in self.alive_players))
        votes = {}
        for player, (target, data) in zip(self.alive_players, results):
            votes[player.name] = target
            print(
                f"🗳️ {player.name} → {target or '弃票'}；理由：{data.get('reason', '无')}"
            )
        voted_out, vote_count = majority_vote_cn(votes)
        if voted_out == "无人":
            await self.public_update("投票平票或无有效票，本轮无人出局。")
            return None
        await self.public_update(f"投票结果：{voted_out}以{vote_count}票被淘汰出局。")
        return voted_out

    async def run_game(self):
        """运行游戏主循环"""
        try:
            await self.setup_game(9)

            for round_num in range(1, MAX_GAME_ROUND + 1):
                print(f"\n🌙 === 第{round_num}轮游戏开始 ===")

                # 夜晚阶段
                await self.moderator.night_announcement(round_num)

                # 狼人击杀
                killed_player = await self.werewolf_phase(round_num)

                # 预言家查验
                await self.seer_phase()

                # 女巫行动
                final_killed, poisoned_player = await self.witch_phase(killed_player)

                # 更新死亡玩家
                night_deaths = list(
                    dict.fromkeys(p for p in [final_killed, poisoned_player] if p)
                )
                self.update_alive_players(night_deaths)

                # 死亡公告
                await self.public_update(
                    f"昨夜出局：{'、'.join(night_deaths) if night_deaths else '无人'}。存活玩家：{format_player_list(self.alive_players)}"
                )

                # 检查胜利条件
                winner = check_winning_cn(self.alive_players, self.roles)
                if winner:
                    await self.moderator.game_over_announcement(winner)
                    return

                # 白天阶段
                voted_out = await self.day_phase(round_num)

                # 猎人技能
                hunter_shot = await self.hunter_phase(voted_out)

                # 更新死亡玩家
                day_deaths = [p for p in [voted_out, hunter_shot] if p]
                self.update_alive_players(day_deaths)
                await self.public_update(
                    f"白天出局：{'、'.join(day_deaths) if day_deaths else '无人'}。存活玩家：{format_player_list(self.alive_players)}"
                )

                # 检查胜利条件
                winner = check_winning_cn(self.alive_players, self.roles)
                if winner:
                    await self.moderator.game_over_announcement(winner)
                    return

                print(
                    f"第{round_num}轮结束，存活玩家：{format_player_list(self.alive_players)}"
                )

        except RuntimeError as e:
            print(f"❌ 游戏运行出错：{e}")
            import traceback

            traceback.print_exc()


async def main():
    """主函数"""
    # 检查环境变量
    if not os.getenv("LLM_API_KEY", "").strip():
        print("❌ 请设置环境变量 LLM_API_KEY")
        return

    print("🎮 欢迎来到三国狼人杀！")

    # 创建并运行游戏
    game = ThreeKingdomsWerewolfGame()
    await game.run_game()


if __name__ == "__main__":
    asyncio.run(main())

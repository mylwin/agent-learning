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
    WerewolfKillModelCN,
    WitchActionModelCN,
    get_hunter_model_cn,
    get_seer_model_cn,
    get_vote_model_cn,
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

    async def werewolf_phase(self, round_num: int):
        """狼人阶段"""
        if not self.werewolves:
            return None

        await self.moderator.announce("🐺 狼人请睁眼，选择今晚要击杀的目标...")

        announcement = await self.moderator.announce(
            f"狼人们，请讨论今晚的击杀目标。存活玩家：{format_player_list(self.alive_players)}"
        )

        # 异步等待狼人们观察公告。gather()方法会等待所有任务完成，或者有一个任务失败。
        await asyncio.gather(*(wolf.observe(announcement) for wolf in self.werewolves))

        # 循环讨论
        for _ in range(MAX_DISCUSSION_ROUND):
            for wolf in self.werewolves:
                # 等待狼人回复讨论消息。reply()回复给定的输入，消耗所有流事件。
                message = await wolf.reply(structured_schema=DiscussionModelCN)
                # 广播给其他狼人
                broadcast = UserMsg(
                    name=wolf.name,
                    content=message.get_text_content()
                    or str(message.structured_output or ""),
                )
                await asyncio.gather(
                    *(
                        other.observe(broadcast)
                        for other in self.werewolves
                        if other is not wolf
                    )
                )

        prompt = await self.moderator.announce("请选择击杀目标")
        kill_votes = await asyncio.gather(
            *(
                wolf.reply(prompt, structured_schema=WerewolfKillModelCN)
                for wolf in self.werewolves
            )
        )
        votes: dict[str, str | None] = {}
        for wolf, vote_msg in zip(self.werewolves, kill_votes):
            target = (vote_msg.structured_output or {}).get("target")
            # 如果没有选择目标，则随机选择一个玩家
            if not target:
                valid_targets = [
                    p.name for p in self.alive_players if p not in self.werewolves
                ]
                target = random.choice(valid_targets) if valid_targets else None
            votes[wolf.name] = target

        # 统计狼人投票结果，返回被击杀的玩家
        killed_player, _ = majority_vote_cn(votes)
        return None if killed_player == "无人" else killed_player

    async def seer_phase(self):
        """预言家阶段"""
        if not self.seer:
            return

        seer_agent = self.seer[0]
        await self.moderator.announce("🔮 预言家请睁眼，选择要查验的玩家...")

        check_result = await seer_agent.reply(
            structured_schema=get_seer_model_cn(self.alive_players)
        )

        # 检查返回结果是否有效
        if (
            check_result is None
            or not hasattr(check_result, "structured_output")
            or check_result.structured_output is None
        ):
            print("⚠️ 预言家查验失败,跳过此阶段")
            return

        target_name = check_result.structured_output.get("target")
        if not target_name:
            print("⚠️ 预言家未选择查验目标,跳过此阶段")
            return

        # 获取查验玩家的角色，默认为村民
        target_role = self.roles.get(target_name, "村民")

        # 告知预言家结果
        result_msg = (
            f"查验结果：{target_name}是{'狼人' if target_role == '狼人' else '好人'}"
        )
        await seer_agent.observe(await self.moderator.announce(result_msg))

    async def witch_phase(self, killed_player: str | None):
        """女巫阶段"""
        if not self.witch:
            return killed_player, None

        witch_agent = self.witch[0]
        await self.moderator.announce("🧙‍♀️ 女巫请睁眼...")

        # 告知女巫死亡信息
        death_info = (
            f"今晚{killed_player}被狼人击杀" if killed_player else "今晚平安无事"
        )
        await witch_agent.observe(await self.moderator.announce(death_info))

        # 女巫行动
        witch_action = await witch_agent.reply(structured_schema=WitchActionModelCN)

        saved_player = None
        poisoned_player = None

        # 检查返回结果是否有效
        if (
            witch_action is None
            or not hasattr(witch_action, "structured_output")
            or witch_action.structured_output is None
        ):
            print("⚠️ 女巫行动失败,视为不使用技能")
        else:
            # 如果女巫使用解药，并且解药技能未使用，而且有玩家死亡，则保存玩家
            if (
                witch_action.structured_output.get("use_antidote")
                and self.witch_has_antidote
            ) and killed_player:
                saved_player = killed_player
                self.witch_has_antidote = False
                await witch_agent.observe(
                    await self.moderator.announce(f"你使用解药救了{killed_player}")
                )

            if (
                witch_action.structured_output.get("use_poison")
                and self.witch_has_poison
            ):
                poisoned_player = witch_action.structured_output.get("target_name")
                if poisoned_player:
                    self.witch_has_poison = False
                    await witch_agent.observe(
                        await self.moderator.announce(
                            f"你使用毒药毒杀了{poisoned_player}"
                        )
                    )

        # 确定最终死亡玩家
        final_killed = killed_player if not saved_player else None

        return final_killed, poisoned_player

    async def hunter_phase(self, shot_by_hunter: str | None):
        """猎人阶段"""
        if not self.hunter:
            return None

        hunter_agent = self.hunter[0]
        if hunter_agent.name == shot_by_hunter:
            await self.moderator.announce("🏹 猎人发动技能，可以带走一名玩家...")

            hunter_action = await hunter_agent.reply(
                structured_schema=get_hunter_model_cn(self.alive_players)
            )

            # 检查返回结果是否有效
            if (
                hunter_action is None
                or not hasattr(hunter_action, "structured_output")
                or hunter_action.structured_output is None
            ):
                print("⚠️ 猎人技能使用失败,视为放弃开枪")
                return None

            if hunter_action.structured_output.get("shoot"):
                target = hunter_action.structured_output.get("target")
                if target:
                    await self.moderator.announce(
                        f"猎人{hunter_agent.name}开枪带走了{target}"
                    )
                    return target
                else:
                    print("⚠️ 猎人选择开枪但未指定目标,视为放弃")
                    return None

        return None

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
            broadcast = UserMsg(
                name=player.name, content=message.get_text_content() or ""
            )
            await asyncio.gather(
                *(
                    other.observe(broadcast)
                    for other in self.alive_players
                    if other is not player
                )
            )

        prompt = await self.moderator.announce("请投票选择要淘汰的玩家")
        vote_msgs = await asyncio.gather(
            *(
                player.reply(
                    prompt, structured_schema=get_vote_model_cn(self.alive_players)
                )
                for player in self.alive_players
            )
        )
        votes = {
            player.name: (message.structured_output or {}).get("vote")
            for player, message in zip(self.alive_players, vote_msgs)
        }
        voted_out, vote_count = majority_vote_cn(votes)
        await self.moderator.vote_result_announcement(voted_out, vote_count)
        return None if voted_out == "无人" else voted_out

    async def run_game(self):
        """运行游戏主循环"""
        try:
            await self.setup_game()

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
                night_deaths = [p for p in [final_killed, poisoned_player] if p]
                self.update_alive_players(night_deaths)

                # 死亡公告
                await self.moderator.death_announcement(night_deaths)

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

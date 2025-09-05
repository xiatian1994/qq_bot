"""
命令处理器
"""

import json
import logging
from typing import Dict, Any, List, Optional

from Core.message.builder import MessageBuilder
from ..core.database import DatabaseManager
from ..core.game_manager import GameManager, GameSession
from ..games.gomoku import Gomoku
from ..games.tictactoe import TicTacToe
from ..systems.ai import AISystem
from ..systems.render import RenderSystem


class CommandHandler:
    """命令处理器"""

    def __init__(self, db_manager: DatabaseManager, game_manager: GameManager,
                 render_system: RenderSystem, ai_system: AISystem, logger: logging.Logger):
        self.db_manager = db_manager
        self.game_manager = game_manager
        self.render_system = render_system
        self.ai_system = ai_system
        self.logger = logger
        self.current_bot_id = None  # 当前处理消息的机器人ID

    def set_current_bot_id(self, bot_id: int):
        """设置当前处理消息的机器人ID"""
        self.current_bot_id = bot_id

    async def handle_chess_menu(self, user_id: str, group_id: str, args: List[str]) -> MessageBuilder:
        """处理游戏菜单命令"""
        try:
            return self._show_game_menu(user_id, group_id)

        except Exception as e:
            self.logger.error(f"处理游戏菜单命令失败: {e}")
            return MessageBuilder.text("\n❌ 命令处理失败，请稍后重试")

    async def handle_tictactoe(self, user_id: str, group_id: str, args: List[str],
                               message_data: Dict[str, Any]) -> MessageBuilder:
        """处理井字棋命令"""
        try:
            if not args:
                # 没有参数，开始AI游戏（默认中等难度）
                return await self._start_tictactoe_ai_game(user_id, group_id, ['medium'])

            first_arg = args[0].lower()

            # 检查是否是数字（下棋位置）
            if first_arg.isdigit():
                position = int(first_arg)
                if 1 <= position <= 9:
                    return await self._make_tictactoe_move(user_id, group_id, [first_arg])
                else:
                    return MessageBuilder.text("\n❌ 位置必须是1-9的数字")

            # 检查是否是难度设置
            elif first_arg in ['简单', 'easy']:
                return await self._start_tictactoe_ai_game(user_id, group_id, ['easy'])
            elif first_arg in ['中等', 'medium']:
                return await self._start_tictactoe_ai_game(user_id, group_id, ['medium'])
            elif first_arg in ['困难', 'hard']:
                return await self._start_tictactoe_ai_game(user_id, group_id, ['hard'])

            # 人人对战命令
            elif first_arg in ['对战', 'pvp', 'start']:
                return await self._start_tictactoe_pvp(user_id, group_id)
            elif first_arg in ['加入', 'join']:
                return await self._join_tictactoe_pvp(user_id, group_id)

            # 其他命令
            elif first_arg in ['状态', 'status']:
                return self._show_waiting_status(user_id, group_id)
            elif first_arg == 'help' or first_arg == '帮助':
                return self._show_tictactoe_help()
            elif first_arg == 'ai':
                return await self._start_tictactoe_ai_game(user_id, group_id, args[1:])
            else:
                return MessageBuilder.text("\n❌ 未知的井字棋操作，请使用 游戏菜单 查看帮助")

        except Exception as e:
            self.logger.error(f"处理井字棋命令失败: {e}")
            return MessageBuilder.text("\n❌ 命令处理失败，请稍后重试")

    async def handle_gomoku(self, user_id: str, group_id: str, args: List[str],
                            message_data: Dict[str, Any]) -> MessageBuilder:
        """处理五子棋命令"""
        try:
            if not args:
                # 没有参数，开始AI游戏（默认中等难度）
                return await self._start_gomoku_ai_game(user_id, group_id, ['medium'])

            first_arg = args[0].upper()

            # 检查是否是坐标格式（如H8）
            if len(first_arg) >= 2 and first_arg[0].isalpha() and first_arg[1:].isdigit():
                return await self._make_gomoku_move(user_id, group_id, [first_arg])

            first_arg_lower = args[0].lower()

            # 检查是否是难度设置
            if first_arg_lower in ['简单', 'easy']:
                return await self._start_gomoku_ai_game(user_id, group_id, ['easy'])
            elif first_arg_lower in ['中等', 'medium']:
                return await self._start_gomoku_ai_game(user_id, group_id, ['medium'])
            elif first_arg_lower in ['困难', 'hard']:
                return await self._start_gomoku_ai_game(user_id, group_id, ['hard'])

            # 人人对战命令
            elif first_arg_lower in ['对战', 'pvp', 'start']:
                return await self._start_gomoku_pvp(user_id, group_id)
            elif first_arg_lower in ['加入', 'join']:
                return await self._join_gomoku_pvp(user_id, group_id)

            # 其他命令
            elif first_arg_lower == 'help' or first_arg_lower == '帮助':
                return self._show_gomoku_help()
            elif first_arg_lower == 'ai':
                return await self._start_gomoku_ai_game(user_id, group_id, args[1:])
            else:
                return MessageBuilder.text("\n❌ 未知的五子棋操作，请使用 游戏菜单 查看帮助")

        except Exception as e:
            self.logger.error(f"处理五子棋命令失败: {e}")
            return MessageBuilder.text("\n❌ 命令处理失败，请稍后重试")

    async def handle_surrender(self, user_id: str, group_id: str) -> MessageBuilder:
        """处理认输命令"""
        try:

            # 查找用户当前的游戏
            game = self.game_manager.get_user_game(user_id, group_id)
            if not game:
                # 检查是否在等待匹配
                ttt_removed = self.game_manager.remove_waiting_player(user_id, group_id, 'tictactoe')
                gomoku_removed = self.game_manager.remove_waiting_player(user_id, group_id, 'gomoku')

                if ttt_removed or gomoku_removed:
                    game_type = "井字棋" if ttt_removed else "五子棋"
                    return MessageBuilder.text(f"\n🏳️ 已取消{game_type}对战等待")
                else:
                    return MessageBuilder.text("\n❌ 您当前没有进行中的游戏或等待中的对战")

            # 获取游戏类型名称
            game_type_name = "井字棋" if game.game_type == "tictactoe" else "五子棋"

            # 处理认输
            if game.is_ai_game:
                # AI游戏，AI获胜
                # AI游戏中，玩家认输意味着AI获胜，但我们在统计中记录为玩家失败
                winner_id = 'AI'
                game.finish_game(winner_id=winner_id)

                # 保存游戏结果
                game_data = json.dumps(game.game_state.to_dict() if game.game_state else {})
                await self._save_game_result(game, winner_id, game_data)

                self.game_manager.remove_game(game.game_id)
                return MessageBuilder.text(f"\n🏳️ 您已认输，{game_type_name}游戏结束")
            else:
                # 人人对战，对手获胜
                opponent_id = game.get_opponent(user_id)
                game.finish_game(winner_id=opponent_id)

                # 保存游戏结果
                game_data = json.dumps(game.game_state.to_dict() if game.game_state else {})
                await self._save_game_result(game, opponent_id, game_data)

                self.game_manager.remove_game(game.game_id)
                return MessageBuilder.text(f"\n🏳️ 您已认输，对手获胜！{game_type_name}游戏结束")

        except Exception as e:
            self.logger.error(f"处理认输命令失败: {e}")
            return MessageBuilder.text("\n❌ 认输失败，请稍后重试")

    def _show_waiting_status(self, user_id: str, group_id: str) -> MessageBuilder:
        """显示等待状态"""
        try:
            # 检查当前游戏
            current_game = self.game_manager.get_user_game(user_id, group_id)
            if current_game:
                game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"
                return MessageBuilder.text(f"\n🎮 您正在进行{game_type_name}游戏")

            # 检查等待状态
            ttt_waiting_time = self.game_manager.get_waiting_time(user_id, group_id, 'tictactoe')
            gomoku_waiting_time = self.game_manager.get_waiting_time(user_id, group_id, 'gomoku')

            if ttt_waiting_time is not None:
                remaining_time = max(0, 60 - ttt_waiting_time)
                return MessageBuilder.text(f"""
⏳ 井字棋等待状态

👤 等待玩家: 用户{user_id}
⏰ 已等待: {ttt_waiting_time // 60}分{ttt_waiting_time % 60}秒
⏰ 剩余时间: {remaining_time // 60}分{remaining_time % 60}秒

💡 其他玩家发送 # 加入 即可开始游戏
🏳️ 回复『认输』可以取消等待""")

            elif gomoku_waiting_time is not None:
                remaining_time = max(0, 60 - gomoku_waiting_time)
                return MessageBuilder.text(f"""
⏳ 五子棋等待状态

👤 等待玩家: 用户{user_id}
⏰ 已等待: {gomoku_waiting_time // 60}分{gomoku_waiting_time % 60}秒
⏰ 剩余时间: {remaining_time // 60}分{remaining_time % 60}秒

💡 其他玩家发送 f 加入 即可开始游戏
🏳️ 回复『认输』可以取消等待""")

            else:
                return MessageBuilder.text("\n📋 您当前没有进行中的游戏或等待中的对战")

        except Exception as e:
            self.logger.error(f"显示等待状态失败: {e}")
            return MessageBuilder.text("\n❌ 获取状态失败，请稍后重试")

    def _get_bot_app_id(self, bot_id: int = None) -> str:
        """获取机器人APP ID"""
        try:
            # 如果没有传入bot_id，使用当前的bot_id
            if bot_id is None:
                bot_id = self.current_bot_id

            # 尝试从bot_manager获取指定机器人的APP ID
            from BluePrints.admin.bots import get_bot_manager
            bot_manager = get_bot_manager()

            if bot_manager and hasattr(bot_manager, 'adapters'):
                # 如果指定了bot_id，优先获取该机器人的APP ID
                if bot_id and bot_id in bot_manager.adapters:
                    adapter = bot_manager.adapters[bot_id]
                    if hasattr(adapter, 'app_id') and adapter.app_id:
                        return str(adapter.app_id)

                # 否则获取第一个可用的适配器
                for current_bot_id, adapter in bot_manager.adapters.items():
                    if hasattr(adapter, 'app_id') and adapter.app_id:
                        return str(adapter.app_id)

            # 如果无法从适配器获取，尝试从数据库获取
            try:
                from Models.SQL.Bot import Bot
                if bot_id:
                    # 获取指定机器人的APP ID
                    bot = Bot.query.filter_by(id=bot_id, is_active=True).first()
                else:
                    # 获取第一个激活的机器人
                    bot = Bot.query.filter_by(is_active=True).first()

                if bot and bot.app_id:
                    return str(bot.app_id)
            except:
                pass

            # 默认返回示例APP ID
            return '102019618'

        except Exception as e:
            self.logger.error(f"获取机器人APP ID失败: {e}")
            return '102019618'  # 返回默认值

    def _show_game_menu(self, user_id: str, group_id: str) -> MessageBuilder:
        """显示游戏菜单"""
        # 检查用户是否有进行中的游戏
        current_game = self.game_manager.get_user_game(user_id, group_id)

        menu_text = """🎮 棋类游戏菜单

🎯 快速游戏：
• # - 井字棋AI对战
• # 对战 - 井字棋人人对战
• f - 五子棋AI对战
• f 对战 - 五子棋人人对战

📊 游戏功能：
• 游戏状态 - 查看当前状态
• 游戏信息 - 查看个人信息
• 游戏排行榜 - 查看群组排行
• 认输 - 认输当前游戏

🎲 难度选择：
• # 简单/中等/困难 - 井字棋AI难度
• f 简单/中等/困难 - 五子棋AI难度"""

        if current_game:
            game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"
            menu_text += f"\n\n🎲 当前游戏：\n正在进行 {game_type_name} 游戏"

            if current_game.is_player_turn(user_id):
                menu_text += " (轮到您下棋)"
            else:
                menu_text += " (等待对手)"

        return MessageBuilder.text(menu_text)

    async def _show_game_status_text(self, user_id: str, group_id: str) -> MessageBuilder:
        """显示游戏状态（文字版）"""
        try:
            # 检查当前游戏
            current_game = self.game_manager.get_user_game(user_id, group_id)
            if current_game:
                game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"
                status_text = f"🎮 您正在进行{game_type_name}游戏\n"

                if current_game.is_ai_game:
                    status_text += "🤖 对手：AI\n"
                else:
                    opponent_id = current_game.get_opponent(user_id)
                    status_text += f"👤 对手：用户{opponent_id}\n"

                if current_game.is_player_turn(user_id):
                    status_text += "⏰ 轮到您下棋"
                else:
                    status_text += "⏳ 等待对手下棋"

                return MessageBuilder.text(status_text)

            # 检查等待状态
            ttt_waiting_time = self.game_manager.get_waiting_time(user_id, group_id, 'tictactoe')
            gomoku_waiting_time = self.game_manager.get_waiting_time(user_id, group_id, 'gomoku')

            if ttt_waiting_time is not None:
                remaining_time = max(0, 60 - ttt_waiting_time)
                return MessageBuilder.text(f"""
⏳ 井字棋等待状态

👤 等待玩家: 用户{user_id}
⏰ 已等待: {ttt_waiting_time // 60}分{ttt_waiting_time % 60}秒
⏰ 剩余时间: {remaining_time // 60}分{remaining_time % 60}秒""")

            elif gomoku_waiting_time is not None:
                remaining_time = max(0, 60 - gomoku_waiting_time)
                return MessageBuilder.text(f"""
⏳ 五子棋等待状态

👤 等待玩家: 用户{user_id}
⏰ 已等待: {gomoku_waiting_time // 60}分{gomoku_waiting_time % 60}秒
⏰ 剩余时间: {remaining_time // 60}分{remaining_time % 60}秒""")

            else:
                return MessageBuilder.text("📋 您当前没有进行中的游戏或等待中的对战")

        except Exception as e:
            self.logger.error(f"显示游戏状态失败: {e}")
            return MessageBuilder.text("\n❌ 获取状态失败，请稍后重试")

    async def _show_user_stats_html(self, user_id: str, group_id: str) -> MessageBuilder:
        """显示用户游戏信息（HTML版）"""
        try:
            # 获取用户统计数据
            ttt_stats = self.db_manager.get_user_stats(user_id, group_id, 'tictactoe')
            gomoku_stats = self.db_manager.get_user_stats(user_id, group_id, 'gomoku')

            # 准备HTML数据
            html_data = {
                'user_id': user_id,
                'bot_app_id': self._get_bot_app_id(),
                'ttt_stats': {
                    'total_games': ttt_stats.total_games if ttt_stats else 0,
                    'wins': ttt_stats.wins if ttt_stats else 0,
                    'losses': ttt_stats.losses if ttt_stats else 0,
                    'draws': ttt_stats.draws if ttt_stats else 0,
                    'win_rate': round((
                                                  ttt_stats.wins / ttt_stats.total_games * 100) if ttt_stats and ttt_stats.total_games > 0 else 0,
                                      1),
                    'best_streak': ttt_stats.best_streak if ttt_stats else 0,
                    'current_streak': ttt_stats.current_streak if ttt_stats else 0,
                },
                'gomoku_stats': {
                    'total_games': gomoku_stats.total_games if gomoku_stats else 0,
                    'wins': gomoku_stats.wins if gomoku_stats else 0,
                    'losses': gomoku_stats.losses if gomoku_stats else 0,
                    'draws': gomoku_stats.draws if gomoku_stats else 0,
                    'win_rate': round((
                                                  gomoku_stats.wins / gomoku_stats.total_games * 100) if gomoku_stats and gomoku_stats.total_games > 0 else 0,
                                      1),
                    'best_streak': gomoku_stats.best_streak if gomoku_stats else 0,
                    'current_streak': gomoku_stats.current_streak if gomoku_stats else 0,
                }
            }

            # 渲染HTML
            image_data = await self.render_system.render_to_image('user_stats.html', html_data, width=600)

            if image_data:
                caption = f"\n🎮 游戏信息"
                return MessageBuilder.image(base64_data=image_data, caption=caption)
            else:
                # 回退到文字版本
                return self._show_user_stats_text(ttt_stats, gomoku_stats, user_id)

        except Exception as e:
            self.logger.error(f"显示用户统计失败: {e}")
            return MessageBuilder.text("\n❌ 获取游戏信息失败，请稍后重试")

    def _show_user_stats_text(self, ttt_stats, gomoku_stats, user_id: str) -> MessageBuilder:
        """显示用户统计"""
        stats_text = f"🎮 游戏信息\n\n"

        # 井字棋统计
        if ttt_stats and ttt_stats.total_games > 0:
            win_rate = round(ttt_stats.wins / ttt_stats.total_games * 100, 1)
            stats_text += f"🎯 井字棋：\n"
            stats_text += f"• 总局数：{ttt_stats.total_games}\n"
            stats_text += f"• 胜率：{win_rate}% ({ttt_stats.wins}胜{ttt_stats.losses}负{ttt_stats.draws}平)\n"
            stats_text += f"• 最佳连胜：{ttt_stats.best_streak}\n"
            stats_text += f"• 当前连胜：{ttt_stats.current_streak}\n\n"
        else:
            stats_text += "🎯 井字棋：暂无记录\n\n"

        # 五子棋统计
        if gomoku_stats and gomoku_stats.total_games > 0:
            win_rate = round(gomoku_stats.wins / gomoku_stats.total_games * 100, 1)
            stats_text += f"🎲 五子棋：\n"
            stats_text += f"• 总局数：{gomoku_stats.total_games}\n"
            stats_text += f"• 胜率：{win_rate}% ({gomoku_stats.wins}胜{gomoku_stats.losses}负{gomoku_stats.draws}平)\n"
            stats_text += f"• 最佳连胜：{gomoku_stats.best_streak}\n"
            stats_text += f"• 当前连胜：{gomoku_stats.current_streak}"
        else:
            stats_text += "🎲 五子棋：暂无记录"

        return MessageBuilder.text(stats_text)

    async def _show_ranking_html(self, group_id: str, args: List[str]) -> MessageBuilder:
        """显示排行榜（HTML版）"""
        try:
            # 获取两种游戏的排行榜数据
            ttt_rankings = self.db_manager.get_group_ranking(group_id, 'tictactoe', limit=10)
            gomoku_rankings = self.db_manager.get_group_ranking(group_id, 'gomoku', limit=10)

            # 准备HTML数据
            html_data = {
                'group_id': group_id,
                'bot_app_id': self._get_bot_app_id(),
                'ttt_rankings': [],
                'gomoku_rankings': []
            }

            # 处理井字棋排行榜
            for i, stats in enumerate(ttt_rankings, 1):
                win_rate = round((stats.wins / stats.total_games * 100) if stats.total_games > 0 else 0, 1)
                html_data['ttt_rankings'].append({
                    'rank': i,
                    'user_id': stats.user_id,
                    'total_games': stats.total_games,
                    'wins': stats.wins,
                    'losses': stats.losses,
                    'draws': stats.draws,
                    'win_rate': win_rate,
                    'best_streak': stats.best_streak
                })

            # 处理五子棋排行榜
            for i, stats in enumerate(gomoku_rankings, 1):
                win_rate = round((stats.wins / stats.total_games * 100) if stats.total_games > 0 else 0, 1)
                html_data['gomoku_rankings'].append({
                    'rank': i,
                    'user_id': stats.user_id,
                    'total_games': stats.total_games,
                    'wins': stats.wins,
                    'losses': stats.losses,
                    'draws': stats.draws,
                    'win_rate': win_rate,
                    'best_streak': stats.best_streak
                })

            # 渲染HTML
            image_data = await self.render_system.render_to_image('ranking.html', html_data, width=800)

            if image_data:
                caption = f"\n🏆 群组排行榜 TOP10"
                return MessageBuilder.image(base64_data=image_data, caption=caption)
            else:
                # 回退到文字版本
                return self._show_ranking_text(ttt_rankings, gomoku_rankings)

        except Exception as e:
            self.logger.error(f"显示排行榜失败: {e}")
            return MessageBuilder.text("\n❌ 获取排行榜失败，请稍后重试")

    def _show_ranking_text(self, ttt_rankings, gomoku_rankings) -> MessageBuilder:
        """显示排行榜（文字版本，作为HTML失败时的回退）"""
        ranking_text = "🏆 群组排行榜 TOP10\n\n"

        # 井字棋排行榜
        ranking_text += "🎯 井字棋排行榜：\n"
        if ttt_rankings:
            for i, stats in enumerate(ttt_rankings[:10], 1):
                win_rate = round((stats.wins / stats.total_games * 100) if stats.total_games > 0 else 0, 1)
                ranking_text += f"{i}. 用户{stats.user_id} - {win_rate}% ({stats.wins}胜)\n"
        else:
            ranking_text += "暂无数据\n"

        ranking_text += "\n🎲 五子棋排行榜：\n"
        if gomoku_rankings:
            for i, stats in enumerate(gomoku_rankings[:10], 1):
                win_rate = round((stats.wins / stats.total_games * 100) if stats.total_games > 0 else 0, 1)
                ranking_text += f"{i}. 用户{stats.user_id} - {win_rate}% ({stats.wins}胜)\n"
        else:
            ranking_text += "暂无数据"

        return MessageBuilder.text(ranking_text)

    def _show_help(self) -> MessageBuilder:
        """显示详细帮助"""
        help_text = """🎮 棋类游戏详细帮助

🎯 井字棋 (TicTacToe)：
• # - 开始AI对战
• # 对战 - 发起人人对战
• # 加入 - 加入人人对战
• # <位置> - 下棋，位置为1-9
• # [简单/中等/困难] - 指定AI难度

🎯 五子棋 (Gomoku)：
• f - 开始AI对战
• f 对战 - 发起人人对战
• f 加入 - 加入人人对战
• f <坐标> - 下棋，如 H8
• f [简单/中等/困难] - 指定AI难度

📊 统计功能：
• 游戏信息 - 个人游戏统计
• 游戏排行榜 - 群组排行榜
• 游戏状态 - 当前游戏状态

🎮 游戏规则：
• 井字棋：3x3棋盘，连成3个获胜
• 五子棋：15x15棋盘，连成5个获胜
• 支持人机对战和玩家对战

💡 使用技巧：
• 游戏会自动超时清理（10分钟无操作）
• 可以随时使用 chess surrender 认输
• AI有三个难度级别可选择"""

        return MessageBuilder.text(help_text)

    def _show_tictactoe_help(self) -> MessageBuilder:
        """显示井字棋帮助"""
        help_text = """
🎯 井字棋游戏帮助

🎮 游戏规则：
• 3x3棋盘，玩家轮流下棋
• 先连成3个的玩家获胜
• X先手，O后手

📝 命令格式：
• # - 开始AI对战（默认中等难度）
• # <位置> - 下棋，位置1-9
• # [难度] - 指定难度开始AI对战
• # 对战 - 发起人人对战（等待1分钟）
• # 加入 - 加入人人对战
• 游戏状态 - 查看当前游戏或等待状态
• 认输 - 认输当前游戏或取消等待

🎯 位置编号：
1 2 3
4 5 6
7 8 9

🤖 AI难度：
• 简单 - 随机下棋
• 中等 - 基本策略（默认）
• 困难 - 高级算法

💡 示例：
• # 对战 - 发起人人对战
• # 5 - 在中心位置下棋
• # 困难 - 与困难AI对战"""

        return MessageBuilder.text(help_text)

    def _show_gomoku_help(self) -> MessageBuilder:
        """显示五子棋帮助"""
        help_text = """
🎯 五子棋游戏帮助

🎮 游戏规则：
• 15x15棋盘，玩家轮流下棋
• 先连成5个的玩家获胜
• 黑棋先手，白棋后手

📝 命令格式：
• f - 开始AI对战（默认中等难度）
• f <坐标> - 下棋，如H8
• f [难度] - 指定难度开始AI对战
• f 对战 - 发起人人对战（等待1分钟）
• f 加入 - 加入人人对战
• 认输 - 认输当前游戏或取消等待

🎯 坐标格式：
• 列用字母A-O表示
• 行用数字1-15表示
• 如：H8表示第8列第8行

🤖 AI难度：
• 简单 - 随机下棋
• 中等 - 基本策略（默认）
• 困难 - 高级算法

💡 示例：
• f H8 - 在H8位置下棋
• f 困难 - 与困难AI对战"""

        return MessageBuilder.text(help_text)

    async def _show_game_status(self, user_id: str, group_id: str) -> MessageBuilder:
        """显示游戏状态"""
        current_game = self.game_manager.get_user_game(user_id, group_id)

        if not current_game:
            return MessageBuilder.text("❌ 您当前没有进行中的游戏")

        game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"

        # 获取对手信息
        opponent_id = current_game.get_opponent(user_id)
        opponent_name = "AI" if opponent_id == "AI" else f"玩家{opponent_id}"

        # 构建状态信息
        status_text = f"""🎮 当前游戏状态

🎯 游戏类型：{game_type_name}
👥 对手：{opponent_name}
⏱️ 开始时间：{current_game.start_time.strftime('%H:%M:%S')}
🎲 步数：{current_game.moves_count}
🎯 当前轮次：{"您的回合" if current_game.is_player_turn(user_id) else "对手回合"}

📋 操作提示：
• 使用 {current_game.game_type} move <位置> 下棋
• 使用 chess surrender 认输"""

        return MessageBuilder.text(status_text)

    async def _show_user_stats(self, user_id: str, group_id: str) -> MessageBuilder:
        """显示用户统计"""
        try:
            # 获取井字棋统计
            ttt_stats = self.db_manager.get_user_stats(user_id, group_id, 'tictactoe')
            gomoku_stats = self.db_manager.get_user_stats(user_id, group_id, 'gomoku')

            stats_text = f"📊 个人游戏统计\n\n"

            # 井字棋统计
            if ttt_stats and ttt_stats.total_games > 0:
                win_rate = (ttt_stats.wins / ttt_stats.total_games * 100) if ttt_stats.total_games > 0 else 0
                stats_text += f"""🎯 井字棋：
• 总局数：{ttt_stats.total_games}
• 胜利：{ttt_stats.wins} \n 失败：{ttt_stats.losses} \n 平局：{ttt_stats.draws}
• 胜率：{win_rate:.1f}%
• 最佳连胜：{ttt_stats.best_streak}
• 当前连胜：{ttt_stats.current_streak}

"""
            else:
                stats_text += "🎯 井字棋：暂无游戏记录\n\n"

            # 五子棋统计
            if gomoku_stats and gomoku_stats.total_games > 0:
                win_rate = (gomoku_stats.wins / gomoku_stats.total_games * 100) if gomoku_stats.total_games > 0 else 0
                stats_text += f"""🎯 五子棋：
• 总局数：{gomoku_stats.total_games}
• 胜利：{gomoku_stats.wins} \n 失败：{gomoku_stats.losses} \n 平局：{gomoku_stats.draws}
• 胜率：{win_rate:.1f}%
• 最佳连胜：{gomoku_stats.best_streak}
• 当前连胜：{gomoku_stats.current_streak}"""
            else:
                stats_text += "🎯 五子棋：暂无游戏记录"

            return MessageBuilder.text(stats_text)

        except Exception as e:
            self.logger.error(f"获取用户统计失败: {e}")
            return MessageBuilder.text("❌ 获取统计数据失败")

    async def _show_ranking(self, group_id: str, args: List[str]) -> MessageBuilder:
        """显示排行榜"""
        try:
            game_type = args[0] if args else 'tictactoe'
            if game_type not in ['tictactoe', 'gomoku']:
                return MessageBuilder.text("❌ 请指定游戏类型：tictactoe 或 gomoku")

            rankings = self.db_manager.get_group_ranking(group_id, game_type, 10)

            if not rankings:
                game_name = "井字棋" if game_type == "tictactoe" else "五子棋"
                return MessageBuilder.text(f"❌ 本群暂无{game_name}游戏记录")

            game_name = "井字棋" if game_type == "tictactoe" else "五子棋"
            rank_text = f"🏆 {game_name}排行榜\n\n"

            for i, stats in enumerate(rankings, 1):
                win_rate = (stats.wins / stats.total_games * 100) if stats.total_games > 0 else 0
                user_display = f"用户{stats.user_id}"

                if i <= 3:
                    medals = ["🥇", "🥈", "🥉"]
                    rank_text += f"{medals[i - 1]} {user_display}\n"
                else:
                    rank_text += f"{i}. {user_display}\n"

                rank_text += f"   胜利：{stats.wins} \n 胜率：{win_rate:.1f}% \n 连胜：{stats.best_streak}\n\n"

            return MessageBuilder.text(rank_text)

        except Exception as e:
            self.logger.error(f"获取排行榜失败: {e}")
            return MessageBuilder.text("❌ 获取排行榜失败")

    async def _handle_surrender(self, user_id: str, group_id: str) -> MessageBuilder:
        """处理认输"""
        try:
            current_game = self.game_manager.get_user_game(user_id, group_id)

            if not current_game:
                return MessageBuilder.text("❌ 您当前没有进行中的游戏")

            # 确定获胜者
            opponent_id = current_game.get_opponent(user_id)
            winner_id = opponent_id if opponent_id != "AI" else None

            # 保存游戏记录
            game_data = json.dumps(current_game.game_state.to_dict() if current_game.game_state else {})
            await self._save_game_result(current_game, winner_id, game_data)

            # 移除游戏
            self.game_manager.remove_game(current_game.game_id)

            game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"

            if opponent_id == "AI":
                return MessageBuilder.text(f"\n🏳️ 您已认输，{game_type_name}游戏结束")
            else:
                return MessageBuilder.text(f"\n🏳️ 您已认输，对手获胜！{game_type_name}游戏结束")

        except Exception as e:
            self.logger.error(f"处理认输失败: {e}")
            return MessageBuilder.text("❌ 认输处理失败")

    async def _save_game_result(self, session: GameSession, winner_id: Optional[str], game_data: str):
        """保存游戏结果"""
        try:
            # 保存游戏记录
            self.db_manager.save_game_record(
                game_type=session.game_type,
                player1_id=session.player1_id,
                player2_id=session.player2_id,
                group_id=session.group_id,
                winner_id=winner_id,
                moves_count=session.moves_count,
                game_data=game_data,
                is_ai_game=session.is_ai_game
            )

            # 更新用户统计（只对真实玩家）
            if not session.is_ai_game:
                # 更新玩家1统计
                if winner_id == session.player1_id:
                    result1 = 'win'
                elif winner_id is None:
                    result1 = 'draw'
                else:
                    result1 = 'loss'

                self.db_manager.update_user_stats(session.player1_id, session.group_id, session.game_type, result1)

                # 更新玩家2统计
                if winner_id == session.player2_id:
                    result2 = 'win'
                elif winner_id is None:
                    result2 = 'draw'
                else:
                    result2 = 'loss'

                self.db_manager.update_user_stats(session.player2_id, session.group_id, session.game_type, result2)
            else:
                # AI游戏只更新真实玩家统计
                if winner_id == session.player1_id:
                    result = 'win'
                elif winner_id is None:
                    result = 'draw'
                else:
                    result = 'loss'

                self.db_manager.update_user_stats(session.player1_id, session.group_id, session.game_type, result)

        except Exception as e:
            self.logger.error(f"保存游戏结果失败: {e}")

    async def _start_tictactoe_pvp(self, user_id: str, group_id: str) -> MessageBuilder:
        """发起井字棋对战"""
        try:
            # 1. 检查用户是否已经在游戏中
            current_game = self.game_manager.get_user_game(user_id, group_id)
            if current_game:
                game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"
                return MessageBuilder.text(f"\n❌ 您正在进行{game_type_name}游戏，请先完成或认输")

            # 2. 检查用户是否已经在等待队列中
            current_waiting_players = self.game_manager.get_waiting_players(group_id, 'tictactoe')
            if user_id in current_waiting_players:
                waiting_time = self.game_manager.get_waiting_time(user_id, group_id, 'tictactoe') or 0
                remaining_time = max(0, 60 - waiting_time)
                if remaining_time > 0:
                    return MessageBuilder.text(f"""
⏳ 您已经在井字棋等待队列中

👤 等待玩家: 用户{user_id}
⏰ 已等待: {waiting_time // 60}分{waiting_time % 60}秒
⏰ 剩余时间: {remaining_time // 60}分{remaining_time % 60}秒

💡 请耐心等待其他玩家加入
🏳️ 发送 认输 可以取消等待""")

            # 3. 尝试匹配对手
            opponent_id = self.game_manager.add_waiting_player(user_id, group_id, 'tictactoe')

            if opponent_id:
                # 找到对手，开始游戏
                return await self._create_tictactoe_pvp_game(user_id, opponent_id, group_id)
            else:
                # 没有对手，进入等待状态
                return MessageBuilder.text(f"""
🎮 井字棋对战房间已创建！

👤 发起者: 用户{user_id}
⏳ 等待对手加入...
⏰ 等待时间: 1分钟（超时自动取消）

💡 其他玩家发送 # 加入 来加入对战
🏳️ 发送 认输 可以取消等待""")

        except Exception as e:
            self.logger.error(f"发起井字棋对战失败: {e}")
            return MessageBuilder.text("\n❌ 发起对战失败，请稍后重试")

    async def _join_tictactoe_pvp(self, user_id: str, group_id: str) -> MessageBuilder:
        """加入井字棋对战"""
        try:
            # 1. 检查用户是否已经在游戏中
            current_game = self.game_manager.get_user_game(user_id, group_id)
            if current_game:
                game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"
                return MessageBuilder.text(f"\n❌ 您正在进行{game_type_name}游戏，请先完成或认输")

            # 2. 检查用户是否已经在等待队列中
            current_waiting_players = self.game_manager.get_waiting_players(group_id, 'tictactoe')
            if user_id in current_waiting_players:
                waiting_time = self.game_manager.get_waiting_time(user_id, group_id, 'tictactoe') or 0
                remaining_time = max(0, 60 - waiting_time)
                if remaining_time > 0:
                    return MessageBuilder.text(f"""
⏳ 您已经在井字棋等待队列中

👤 等待玩家: 用户{user_id}
⏰ 已等待: {waiting_time // 60}分{waiting_time % 60}秒
⏰ 剩余时间: {remaining_time // 60}分{remaining_time % 60}秒

💡 请耐心等待其他玩家加入
🏳️ 发送 认输 可以取消等待""")
                else:
                    # 等待已超时，从队列中移除
                    self.game_manager.remove_waiting_player(user_id, group_id, 'tictactoe')
                    return MessageBuilder.text(f"""
⏰ 您的等待已超时，已自动退出队列

💡 请重新发送 # 对战 创建新的对战房间
💡 或等待其他玩家创建房间后发送 # 加入""")

            # 3. 尝试匹配对手
            opponent_id = self.game_manager.add_waiting_player(user_id, group_id, 'tictactoe')

            if opponent_id:
                # 找到对手，开始游戏
                return await self._create_tictactoe_pvp_game(opponent_id, user_id, group_id)
            else:
                # 没有等待的对手，检查是否成功加入队列
                updated_waiting_players = self.game_manager.get_waiting_players(group_id, 'tictactoe')
                if user_id in updated_waiting_players:
                    return MessageBuilder.text(f"""
🎮 没有等待中的对战房间，已为您创建新房间！

👤 房间创建者: 用户{user_id}
⏳ 等待其他玩家加入...
⏰ 等待时间: 1分钟（超时自动取消）

💡 其他玩家发送 # 加入 即可开始对战
🏳️ 发送 认输 可以取消等待""")
                else:
                    # 这种情况理论上不应该发生，但作为保险
                    return MessageBuilder.text(f"""
❌ 加入对战失败

💡 请发送 # 对战 创建对战房间""")

        except Exception as e:
            self.logger.error(f"加入井字棋对战失败: {e}")
            return MessageBuilder.text("\n❌ 加入对战失败，请稍后重试")

    async def _create_tictactoe_pvp_game(self, player1_id: str, player2_id: str, group_id: str) -> MessageBuilder:
        """创建井字棋PvP游戏"""
        try:
            from ..games.tictactoe import TicTacToe

            # 创建游戏会话
            session = self.game_manager.create_game(
                game_type='tictactoe',
                player1_id=player1_id,
                player2_id=player2_id,
                group_id=group_id,
                bot_id=0
            )

            # 创建游戏实例
            game = TicTacToe(player1_id, player2_id)
            session.game_state = game

            # 生成棋盘图片
            try:
                html_data = game.get_html_data()
                # 添加机器人APP ID用于头像显示
                html_data['bot_app_id'] = self._get_bot_app_id()
                image_data = await self.render_system.render_to_image('tictactoe_board.html', html_data, width=600)

                if image_data:
                    caption = f"\n🎮 井字棋对战开始！\n👥 X: 用户{player1_id} \n O: 用户{player2_id}\n💡 轮到 X 下棋，使用 # <位置> 命令"
                    return MessageBuilder.image(base64_data=image_data, caption=caption)
                else:
                    # 图片生成失败，返回文本
                    return MessageBuilder.text(f"""
🎮 井字棋对战开始！

👥 玩家：
• X (先手): 用户{player1_id}
• O (后手): 用户{player2_id}

{game.get_board_display()}

💡 轮到 X 下棋，使用 # <位置> 命令""")

            except Exception as render_error:
                self.logger.error(f"渲染井字棋棋盘失败: {render_error}")
                # 渲染失败，返回文本
                return MessageBuilder.text(f"""
🎮 井字棋对战开始！

👥 玩家：
• X (先手): 用户{player1_id}
• O (后手): 用户{player2_id}

{game.get_board_display()}

💡 轮到 X 下棋，使用 # <位置> 命令""")

        except Exception as e:
            self.logger.error(f"创建井字棋PvP游戏失败: {e}")
            return MessageBuilder.text("\n❌ 创建游戏失败，请稍后重试")

    async def _start_gomoku_pvp(self, user_id: str, group_id: str) -> MessageBuilder:
        """发起五子棋对战"""
        try:
            # 1. 检查用户是否已经在游戏中
            current_game = self.game_manager.get_user_game(user_id, group_id)
            if current_game:
                game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"
                return MessageBuilder.text(f"\n❌ 您正在进行{game_type_name}游戏，请先完成或认输")

            # 2. 检查用户是否已经在等待队列中
            current_waiting_players = self.game_manager.get_waiting_players(group_id, 'gomoku')
            if user_id in current_waiting_players:
                waiting_time = self.game_manager.get_waiting_time(user_id, group_id, 'gomoku') or 0
                remaining_time = max(0, 60 - waiting_time)
                if remaining_time > 0:
                    return MessageBuilder.text(f"""
⏳ 您已经在五子棋等待队列中

👤 等待玩家: 用户{user_id}
⏰ 已等待: {waiting_time // 60}分{waiting_time % 60}秒
⏰ 剩余时间: {remaining_time // 60}分{remaining_time % 60}秒

💡 请耐心等待其他玩家加入
🏳️ 发送 认输 可以取消等待""")

            # 3. 尝试匹配对手
            opponent_id = self.game_manager.add_waiting_player(user_id, group_id, 'gomoku')

            if opponent_id:
                # 找到对手，开始游戏
                return await self._create_gomoku_pvp_game(user_id, opponent_id, group_id)
            else:
                # 没有对手，进入等待状态
                return MessageBuilder.text(f"""
🎮 五子棋对战房间已创建！

👤 发起者: 用户{user_id}
⏳ 等待对手加入...
⏰ 等待时间: 1分钟（超时自动取消）

💡 其他玩家发送 f 加入 来加入对战
🏳️ 发送 认输 可以取消等待""")

        except Exception as e:
            self.logger.error(f"发起五子棋对战失败: {e}")
            return MessageBuilder.text("\n❌ 发起对战失败，请稍后重试")

    async def _join_gomoku_pvp(self, user_id: str, group_id: str) -> MessageBuilder:
        """加入五子棋对战"""
        try:
            # 1. 检查用户是否已经在游戏中
            current_game = self.game_manager.get_user_game(user_id, group_id)
            if current_game:
                game_type_name = "井字棋" if current_game.game_type == "tictactoe" else "五子棋"
                return MessageBuilder.text(f"\n❌ 您正在进行{game_type_name}游戏，请先完成或认输")

            # 2. 检查用户是否已经在等待队列中
            current_waiting_players = self.game_manager.get_waiting_players(group_id, 'gomoku')
            if user_id in current_waiting_players:
                waiting_time = self.game_manager.get_waiting_time(user_id, group_id, 'gomoku') or 0
                remaining_time = max(0, 60 - waiting_time)
                if remaining_time > 0:
                    return MessageBuilder.text(f"""
⏳ 您已经在五子棋等待队列中

👤 等待玩家: 用户{user_id}
⏰ 已等待: {waiting_time // 60}分{waiting_time % 60}秒
⏰ 剩余时间: {remaining_time // 60}分{remaining_time % 60}秒

💡 请耐心等待其他玩家加入
🏳️ 发送 认输 可以取消等待""")
                else:
                    # 等待已超时，从队列中移除
                    self.game_manager.remove_waiting_player(user_id, group_id, 'gomoku')
                    return MessageBuilder.text(f"""
⏰ 您的等待已超时，已自动退出队列

💡 请重新发送 f 对战 创建新的对战房间
💡 或等待其他玩家创建房间后发送 f 加入""")

            # 3. 尝试匹配对手
            opponent_id = self.game_manager.add_waiting_player(user_id, group_id, 'gomoku')

            if opponent_id:
                # 找到对手，开始游戏
                return await self._create_gomoku_pvp_game(opponent_id, user_id, group_id)
            else:
                # 没有等待的对手，检查是否成功加入队列
                updated_waiting_players = self.game_manager.get_waiting_players(group_id, 'gomoku')
                if user_id in updated_waiting_players:
                    return MessageBuilder.text(f"""
🎮 没有等待中的对战房间，已为您创建新房间！

👤 房间创建者: 用户{user_id}
⏳ 等待其他玩家加入...
⏰ 等待时间: 1分钟（超时自动取消）

💡 其他玩家发送 f 加入 即可开始对战
🏳️ 发送 认输 可以取消等待""")
                else:
                    # 这种情况理论上不应该发生，但作为保险
                    return MessageBuilder.text(f"""
❌ 加入对战失败

💡 请发送 f 对战 创建对战房间""")

        except Exception as e:
            self.logger.error(f"加入五子棋对战失败: {e}")
            return MessageBuilder.text("\n❌ 加入对战失败，请稍后重试")

    async def _create_gomoku_pvp_game(self, player1_id: str, player2_id: str, group_id: str) -> MessageBuilder:
        """创建五子棋PvP游戏"""
        try:
            from ..games.gomoku import Gomoku

            # 创建游戏会话
            session = self.game_manager.create_game(
                game_type='gomoku',
                player1_id=player1_id,
                player2_id=player2_id,
                group_id=group_id,
                bot_id=0
            )

            # 创建游戏实例
            game = Gomoku(player1_id, player2_id)
            session.game_state = game

            # 生成棋盘图片
            try:
                html_data = game.get_html_data()
                # 添加机器人APP ID用于头像显示
                html_data['bot_app_id'] = self._get_bot_app_id()
                image_data = await self.render_system.render_to_image('gomoku_board.html', html_data, width=700)

                if image_data:
                    caption = f"\n🎮 五子棋对战开始！\n{player1_id} (●) vs {player2_id} (○)\n轮到 {player1_id} 下棋"
                    return MessageBuilder.image(base64_data=image_data, caption=caption)
                else:
                    # 图片生成失败，使用文本
                    return MessageBuilder.text(f"""
🎮 五子棋对战开始！

● 黑棋: 用户{player1_id}
○ 白棋: 用户{player2_id}

轮到 用户{player1_id} 下棋
请发送坐标，如：f H8""")

            except Exception as e:
                self.logger.error(f"生成五子棋对战棋盘图片失败: {e}")
                # 回退到文本显示
                return MessageBuilder.text(f"""
🎮 五子棋对战开始！

● 黑棋: 用户{player1_id}
○ 白棋: 用户{player2_id}

轮到 用户{player1_id} 下棋
请发送坐标，如：f H8""")

        except Exception as e:
            self.logger.error(f"创建五子棋PvP游戏失败: {e}")
            return MessageBuilder.text("\n❌ 创建游戏失败，请稍后重试")

    async def _start_tictactoe_ai_game(self, user_id: str, group_id: str, args: List[str]) -> MessageBuilder:
        """开始井字棋AI游戏"""
        try:
            # 检查用户是否已经在游戏中
            if self.game_manager.get_user_game(user_id, group_id):
                return MessageBuilder.text("❌ 您已经在其他游戏中，请先完成或认输")

            # 解析难度（支持中文和英文）
            difficulty_input = args[0] if args else 'medium'
            difficulty_map = {
                '简单': 'easy', 'easy': 'easy',
                '中等': 'medium', 'medium': 'medium',
                '困难': 'hard', 'hard': 'hard'
            }
            difficulty = difficulty_map.get(difficulty_input.lower(), difficulty_input.lower())

            if difficulty not in self.ai_system.get_available_difficulties():
                return MessageBuilder.text("❌ 无效的难度级别，请选择：简单(easy)、中等(medium)、困难(hard)")

            # 创建游戏会话
            session = self.game_manager.create_game('tictactoe', user_id, 'AI', group_id, 1)

            # 创建游戏实例
            game = TicTacToe(user_id, 'AI')
            session.game_state = game

            # 生成棋盘图片
            try:
                html_data = game.get_html_data()
                # 添加机器人APP ID用于头像显示
                html_data['bot_app_id'] = self._get_bot_app_id()
                image_data = await self.render_system.render_to_image('tictactoe_board.html', html_data, width=600)

                if image_data:
                    # 简要文字说明
                    difficulty_desc = self.ai_system.get_difficulty_description(difficulty)
                    caption = f"\n🎮 井字棋 vs AI 开始！\n👥 X: 您 \n O: AI ({difficulty_desc})\n💡 轮到您下棋，使用 # <位置> 命令"
                    return MessageBuilder.image(base64_data=image_data, caption=caption)
                else:
                    # 图片生成失败，使用文本
                    difficulty_desc = self.ai_system.get_difficulty_description(difficulty)
                    start_text = f"""
\n🎮 井字棋 vs AI 开始！

👥 玩家：
• X (先手): 您
• O (后手): AI ({difficulty_desc})

{game.get_board_display()}

💡 提示：轮到您下棋，使用 # <位置> 命令下棋"""
                    return MessageBuilder.text(start_text)

            except Exception as e:
                self.logger.error(f"井字棋AI棋盘图片生成失败: {e}")
                # 回退到文本显示
                difficulty_desc = self.ai_system.get_difficulty_description(difficulty)
                start_text = f"""
\n🎮 井字棋 vs AI 开始！

👥 玩家：
• X (先手): 您
• O (后手): AI ({difficulty_desc})

{game.get_board_display()}

💡 提示：轮到您下棋，使用 # <位置> 命令下棋"""
                return MessageBuilder.text(start_text)

        except Exception as e:
            self.logger.error(f"开始井字棋AI游戏失败: {e}")
            return MessageBuilder.text(f"❌ 开始AI游戏失败: {str(e)}")

    async def _make_tictactoe_move(self, user_id: str, group_id: str, args: List[str]) -> MessageBuilder:
        """执行井字棋移动"""

        try:
            # 获取当前游戏
            session = self.game_manager.get_user_game(user_id, group_id)
            if not session or session.game_type != 'tictactoe':
                return MessageBuilder.text("\n❌ 您当前没有进行中的井字棋游戏")

            if not args:
                return MessageBuilder.text("\n❌ 请指定位置，如：# 5")

            try:
                position = int(args[0])
            except ValueError:
                return MessageBuilder.text("\n❌ 位置必须是1-9的数字")

            game = session.game_state
            if not game:
                return MessageBuilder.text("\n❌ 游戏状态异常")

            # 执行移动
            result = game.make_move(user_id, position)
            session.moves_count = game.moves_count

            if result.result.value == 'invalid':
                return MessageBuilder.text(f"{result.message}")

            # 生成棋盘图片
            try:
                html_data = game.get_html_data()
                # 添加机器人APP ID用于头像显示
                html_data['bot_app_id'] = self._get_bot_app_id()
                image_data = await self.render_system.render_to_image('tictactoe_board.html', html_data, width=600)

                if image_data:
                    caption = f"\n🎮 井字棋\n{result.message}"

                    # 检查游戏是否结束
                    if result.result.value in ['win', 'draw']:
                        # 保存游戏结果
                        game_data = json.dumps(game.to_dict())
                        await self._save_game_result(session, result.winner, game_data)

                        # 移除游戏
                        self.game_manager.remove_game(session.game_id)

                        # 游戏结束，直接返回
                        return MessageBuilder.image(base64_data=image_data, caption=caption)

                    # 游戏未结束，先保存玩家移动的图片，稍后可能需要回复两条消息
                    player_move_image = MessageBuilder.image(base64_data=image_data, caption=caption)
                else:
                    # 图片生成失败，使用文本
                    response_text = f"{game.get_board_display()}\n\n{result.message}"

                    # 检查游戏是否结束
                    if result.result.value in ['win', 'draw']:
                        # 保存游戏结果
                        game_data = json.dumps(game.to_dict())
                        await self._save_game_result(session, result.winner, game_data)

                        # 移除游戏
                        self.game_manager.remove_game(session.game_id)

                        # 游戏结束，直接返回
                        return MessageBuilder.text(response_text)

                    # 游戏未结束，先保存玩家移动的文本，稍后可能需要回复两条消息
                    player_move_image = MessageBuilder.text(response_text)

            except Exception as e:
                self.logger.error(f"井字棋移动后图片生成失败: {e}")
                # 回退到文本显示
                response_text = f"{game.get_board_display()}\n\n{result.message}"

                # 检查游戏是否结束
                if result.result.value in ['win', 'draw']:
                    # 保存游戏结果
                    game_data = json.dumps(game.to_dict())
                    await self._save_game_result(session, result.winner, game_data)

                    # 移除游戏
                    self.game_manager.remove_game(session.game_id)

                    # 游戏结束，直接返回
                    return MessageBuilder.text(response_text)

                # 游戏未结束，先保存玩家移动的文本，稍后可能需要回复两条消息
                player_move_image = MessageBuilder.text(response_text)

            # 如果是AI游戏且轮到AI，返回两条消息
            if session.is_ai_game and game.current_player == 'AI':
                # 第一条消息：使用之前保存的玩家移动结果
                first_message = player_move_image

                # AI下棋
                ai_move = self.ai_system.get_ai_move(game, 'medium')

                if ai_move:
                    ai_result = game.make_move('AI', ai_move)
                    session.moves_count = game.moves_count

                    # 准备第二条消息：AI移动结果
                    try:
                        html_data_ai = game.get_html_data()
                        ai_image_data = await self.render_system.render_to_image('tictactoe_board.html', html_data_ai,
                                                                                 width=600)

                        if ai_image_data:
                            second_message = MessageBuilder.image(base64_data=ai_image_data,
                                                                  caption=f"\n🎮 井字棋 \n AI选择了位置 {ai_move}\n{ai_result.message}")
                        else:
                            second_message = MessageBuilder.text(
                                f"{game.get_board_display()}\n\nAI选择了位置 {ai_move}\n{ai_result.message}")
                    except Exception as e:
                        second_message = MessageBuilder.text(
                            f"{game.get_board_display()}\n\nAI选择了位置 {ai_move}\n{ai_result.message}")

                    # 检查AI移动后游戏是否结束
                    if ai_result.result.value in ['win', 'draw']:
                        game_data = json.dumps(game.to_dict())
                        await self._save_game_result(session, ai_result.winner, game_data)
                        self.game_manager.remove_game(session.game_id)

                    # 返回两条消息
                    return [first_message, second_message]
                else:
                    pass
            else:
                # 不是AI游戏或不轮到AI，返回玩家移动的单条消息
                return player_move_image

        except Exception as e:
            self.logger.error(f"执行井字棋移动失败: {e}")
            return MessageBuilder.text("❌ 移动执行失败")

    async def _start_gomoku_ai_game(self, user_id: str, group_id: str, args: List[str]) -> MessageBuilder:
        """开始五子棋AI游戏"""
        try:
            # 检查用户是否已经在游戏中
            if self.game_manager.get_user_game(user_id, group_id):
                return MessageBuilder.text("❌ 您已经在其他游戏中，请先完成或认输")

            # 解析难度（支持中文和英文）
            difficulty_input = args[0] if args else 'medium'
            difficulty_map = {
                '简单': 'easy', 'easy': 'easy',
                '中等': 'medium', 'medium': 'medium',
                '困难': 'hard', 'hard': 'hard'
            }
            difficulty = difficulty_map.get(difficulty_input.lower(), difficulty_input.lower())

            if difficulty not in self.ai_system.get_available_difficulties():
                return MessageBuilder.text("❌ 无效的难度级别，请选择：简单(easy)、中等(medium)、困难(hard)")

            # 创建游戏会话
            session = self.game_manager.create_game('gomoku', user_id, 'AI', group_id, 1)

            # 创建游戏实例
            game = Gomoku(user_id, 'AI')
            session.game_state = game

            # 生成棋盘图片
            try:
                html_data = game.get_html_data()
                # 添加机器人APP ID用于头像显示
                html_data['bot_app_id'] = self._get_bot_app_id()

                image_data = await self.render_system.render_to_image('gomoku_board.html', html_data, width=800)

                if image_data:
                    # 简要文字说明
                    difficulty_desc = self.ai_system.get_difficulty_description(difficulty)
                    caption = f"\n🎮 五子棋 vs AI 开始！\n👥 ●: 您 \n ○: AI ({difficulty_desc})\n💡 轮到您下棋，使用 f <坐标> 命令"
                    return MessageBuilder.image(base64_data=image_data, caption=caption)
                else:
                    # 图片生成失败，使用文本
                    difficulty_desc = self.ai_system.get_difficulty_description(difficulty)
                    start_text = f"""
🎮 五子棋 vs AI 开始！

👥 玩家：
• ● (黑棋先手): 您
• ○ (白棋后手): AI ({difficulty_desc})

{game.get_board_display()}

💡 提示：轮到您下棋，使用 f <坐标> 命令下棋（如：f H8）"""
                    return MessageBuilder.text(start_text)

            except Exception as e:
                self.logger.error(f"五子棋AI棋盘图片生成失败: {e}")
                # 回退到文本显示
                difficulty_desc = self.ai_system.get_difficulty_description(difficulty)
                start_text = f"""
🎮 五子棋 vs AI 开始！

👥 玩家：
• ● (黑棋先手): 您
• ○ (白棋后手): AI ({difficulty_desc})

{game.get_board_display()}

💡 提示：轮到您下棋，使用 f <坐标> 命令下棋（如：f H8）"""
                return MessageBuilder.text(start_text)

        except Exception as e:
            self.logger.error(f"开始五子棋AI游戏失败: {e}")
            return MessageBuilder.text(f"❌ 开始AI游戏失败: {str(e)}")

    async def _make_gomoku_move(self, user_id: str, group_id: str, args: List[str]) -> MessageBuilder:
        """执行五子棋移动"""

        try:
            # 获取当前游戏
            session = self.game_manager.get_user_game(user_id, group_id)
            if not session or session.game_type != 'gomoku':
                return MessageBuilder.text("\n❌ 您当前没有进行中的五子棋游戏")

            if not args:
                return MessageBuilder.text("\n❌ 请指定坐标，如：f H8")

            position = args[0].upper()

            game = session.game_state
            if not game:
                return MessageBuilder.text("❌ 游戏状态异常")

            # 执行移动
            result = game.make_move(user_id, position)
            session.moves_count = game.moves_count

            if result.result.value == 'invalid':
                return MessageBuilder.text(f"❌ {result.message}")

            # 生成棋盘图片
            try:
                html_data = game.get_html_data()
                # 添加机器人APP ID用于头像显示
                html_data['bot_app_id'] = self._get_bot_app_id()

                image_data = await self.render_system.render_to_image('gomoku_board.html', html_data, width=800)

                if image_data:
                    caption = f"🎮 五子棋 - {result.message}"

                    # 检查游戏是否结束
                    if result.result.value in ['win', 'draw']:
                        # 保存游戏结果
                        game_data = json.dumps(game.to_dict())
                        await self._save_game_result(session, result.winner, game_data)

                        # 移除游戏
                        self.game_manager.remove_game(session.game_id)

                        # 游戏结束，直接返回
                        return MessageBuilder.image(base64_data=image_data, caption=caption)

                    # 游戏未结束，先保存玩家移动的图片，稍后可能需要发送两条消息
                    player_move_image = MessageBuilder.image(base64_data=image_data, caption=caption)
                else:
                    # 图片生成失败，使用文本
                    response_text = f"{game.get_board_display()}\n\n{result.message}"

                    # 检查游戏是否结束
                    if result.result.value in ['win', 'draw']:
                        # 保存游戏结果
                        game_data = json.dumps(game.to_dict())
                        await self._save_game_result(session, result.winner, game_data)

                        # 移除游戏
                        self.game_manager.remove_game(session.game_id)

                        # 游戏结束，直接返回
                        return MessageBuilder.text(response_text)

                    # 游戏未结束，先保存玩家移动的文本，稍后可能需要发送两条消息
                    player_move_image = MessageBuilder.text(response_text)

            except Exception as e:
                self.logger.error(f"五子棋移动后图片生成失败: {e}")
                # 回退到文本显示
                response_text = f"{game.get_board_display()}\n\n{result.message}"

                # 检查游戏是否结束
                if result.result.value in ['win', 'draw']:
                    # 保存游戏结果
                    game_data = json.dumps(game.to_dict())
                    await self._save_game_result(session, result.winner, game_data)

                    # 移除游戏
                    self.game_manager.remove_game(session.game_id)

                    # 游戏结束，直接返回
                    return MessageBuilder.text(response_text)

                # 游戏未结束，先保存玩家移动的文本，稍后可能需要发送两条消息
                player_move_image = MessageBuilder.text(response_text)

            # 检查是否是AI游戏且轮到AI
            # 如果是AI游戏且轮到AI，返回两条消息
            if session.is_ai_game and game.current_player == 'AI':

                # 第一条消息：使用之前保存的玩家移动结果
                first_message = player_move_image

                # AI下棋
                ai_move = self.ai_system.get_ai_move(game, 'medium')

                if ai_move:
                    ai_result = game.make_move('AI', ai_move)
                    session.moves_count = game.moves_count

                    # 准备第二条消息：AI移动结果
                    try:
                        html_data_ai = game.get_html_data()
                        ai_image_data = await self.render_system.render_to_image('gomoku_board.html', html_data_ai,
                                                                                 width=800)

                        if ai_image_data:
                            second_message = MessageBuilder.image(base64_data=ai_image_data,
                                                                  caption=f"🎮 五子棋 - AI选择了位置 {ai_move}\n{ai_result.message}")
                        else:
                            second_message = MessageBuilder.text(
                                f"{game.get_board_display()}\n\nAI选择了位置 {ai_move}\n{ai_result.message}")
                    except Exception as e:
                        second_message = MessageBuilder.text(
                            f"{game.get_board_display()}\n\nAI选择了位置 {ai_move}\n{ai_result.message}")

                    # 检查AI移动后游戏是否结束
                    if ai_result.result.value in ['win', 'draw']:
                        game_data = json.dumps(game.to_dict())
                        await self._save_game_result(session, ai_result.winner, game_data)
                        self.game_manager.remove_game(session.game_id)

                    # 返回两条消息
                    return [first_message, second_message]
                else:
                    pass
            else:
                # 不是AI游戏或不轮到AI，返回玩家移动的单条消息
                return player_move_image

        except Exception as e:
            self.logger.error(f"执行五子棋移动失败: {e}")
            return MessageBuilder.text("❌ 移动执行失败")

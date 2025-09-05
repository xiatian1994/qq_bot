"""
棋类游戏插件
支持井字棋、五子棋等多种棋类游戏
"""

import asyncio
import logging

from Core.logging.file_logger import log_error
from Core.message.builder import MessageBuilder
from Core.plugin.base import BasePlugin
from .core.database import DatabaseManager
from .core.game_manager import GameManager
from .handlers.command_handler import CommandHandler
from .systems.ai import AISystem
from .systems.render import RenderSystem


class Plugin(BasePlugin):
    """棋类游戏插件主类"""

    def __init__(self):
        super().__init__()

        # 插件信息
        self.name = "ChessGames"
        self.version = "1.0.0"
        self.description = "棋类游戏插件 - 支持井字棋、五子棋等多种棋类游戏"
        self.author = "Yixuan"

        # 获取系统日志器
        self.logger = logging.getLogger(f"ChessGames.{self.name}")

        # 初始化核心组件
        self.db_manager = DatabaseManager()
        self.game_manager = GameManager()
        self.render_system = RenderSystem()
        self.ai_system = AISystem()

        # 初始化命令处理器
        self.command_handler = CommandHandler(
            db_manager=self.db_manager,
            game_manager=self.game_manager,
            render_system=self.render_system,
            ai_system=self.ai_system,
            logger=self.logger
        )

        # 初始化数据库
        try:
            self.db_manager.init_database()
            self.logger.info("棋类游戏插件数据库初始化完成")
        except Exception as e:
            self.logger.error(f"棋类游戏插件数据库初始化失败: {e}")

        # 注册命令信息
        self.register_command_info('#', '井字棋游戏', '# [难度] 或 # <位置1-9>')
        self.register_command_info('f', '五子棋游戏', 'f [难度] 或 f <坐标>')
        self.register_command_info('游戏菜单', '显示游戏菜单', '游戏菜单')
        self.register_command_info('游戏状态', '查看当前状态', '游戏状态')
        self.register_command_info('游戏信息', '查看个人信息', '游戏信息')
        self.register_command_info('游戏排行榜', '查看群组排行', '游戏排行榜')
        self.register_command_info('认输', '认输当前游戏', '认输')

        # 注册Hook事件处理器
        self.hooks = {
            'message_received': [self.handle_message_hook],
            'bot_start': [self.on_bot_start_hook],
            'bot_stop': [self.on_bot_stop_hook]
        }

        # 命令处理器映射
        self.command_handlers = {
            '#': self.handle_tictactoe,
            'f': self.handle_gomoku,
            '游戏菜单': self.handle_chess_menu,
            '游戏状态': self.handle_game_status,
            '游戏信息': self.handle_game_info,
            '游戏排行榜': self.handle_game_ranking,
            '认输': self.handle_surrender
        }

        # 当前消息数据（用于命令处理器）
        self._current_message_data = None
        self._current_bot_id = None

    def run_async(self, coro):
        """运行异步函数的辅助方法"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                task = asyncio.create_task(coro)
                return task
            else:
                # 如果事件循环未运行，直接运行
                return loop.run_until_complete(coro)
        except RuntimeError:
            # 如果没有事件循环，创建新的
            return asyncio.run(coro)

    def get_user_group_from_message(self, message_data):
        """从消息数据中提取用户ID和群组ID"""
        try:
            user_id = message_data.get('author', {}).get('union_openid')
            group_id = message_data.get('group_openid')
            return user_id, group_id
        except Exception as e:
            self.logger.error(f"提取用户群组信息失败: {e}")
            return None, None

    # ==================== 命令处理方法 ====================

    def handle_tictactoe(self, args):
        """处理井字棋命令"""
        try:
            user_id, group_id = self.get_user_group_from_message(self._current_message_data)
            if not user_id or not group_id:
                return MessageBuilder.text("❌ 无法获取用户或群组信息")

            # 设置当前机器人ID
            self.command_handler.set_current_bot_id(self._current_bot_id)

            return self.run_async(
                self.command_handler.handle_tictactoe(user_id, group_id, args, self._current_message_data))

        except Exception as e:
            self.logger.error(f"井字棋命令处理失败: {e}")
            return MessageBuilder.text("❌ 命令处理失败，请稍后重试")

    def handle_gomoku(self, args):
        """处理五子棋命令"""
        try:
            user_id, group_id = self.get_user_group_from_message(self._current_message_data)
            if not user_id or not group_id:
                return MessageBuilder.text("❌ 无法获取用户或群组信息")

            # 设置当前机器人ID
            self.command_handler.set_current_bot_id(self._current_bot_id)

            return self.run_async(
                self.command_handler.handle_gomoku(user_id, group_id, args, self._current_message_data))

        except Exception as e:
            self.logger.error(f"五子棋命令处理失败: {e}")
            return MessageBuilder.text("❌ 命令处理失败，请稍后重试")

    def handle_chess_menu(self, args):
        """处理chess菜单命令"""
        try:
            user_id, group_id = self.get_user_group_from_message(self._current_message_data)
            if not user_id or not group_id:
                return MessageBuilder.text("❌ 无法获取用户或群组信息")

            # 设置当前机器人ID
            self.command_handler.set_current_bot_id(self._current_bot_id)

            return self.run_async(self.command_handler.handle_chess_menu(user_id, group_id, args))

        except Exception as e:
            self.logger.error(f"chess菜单命令处理失败: {e}")
            return MessageBuilder.text("❌ 命令处理失败，请稍后重试")

    def handle_surrender(self, args):
        """处理认输命令"""
        try:
            user_id, group_id = self.get_user_group_from_message(self._current_message_data)
            if not user_id or not group_id:
                return MessageBuilder.text("❌ 无法获取用户或群组信息")

            # 设置当前机器人ID
            self.command_handler.set_current_bot_id(self._current_bot_id)

            return self.run_async(self.command_handler.handle_surrender(user_id, group_id))

        except Exception as e:
            self.logger.error(f"认输命令处理失败: {e}")
            return MessageBuilder.text("❌ 命令处理失败，请稍后重试")

    def handle_game_status(self, args):
        """处理游戏状态命令"""
        try:
            user_id, group_id = self.get_user_group_from_message(self._current_message_data)
            if not user_id or not group_id:
                return MessageBuilder.text("❌ 无法获取用户或群组信息")

            # 设置当前机器人ID
            self.command_handler.set_current_bot_id(self._current_bot_id)

            return self.run_async(self.command_handler._show_game_status_text(user_id, group_id))

        except Exception as e:
            self.logger.error(f"游戏状态命令处理失败: {e}")
            return MessageBuilder.text("❌ 命令处理失败，请稍后重试")

    def handle_game_info(self, args):
        """处理游戏信息命令"""
        try:
            user_id, group_id = self.get_user_group_from_message(self._current_message_data)
            if not user_id or not group_id:
                return MessageBuilder.text("❌ 无法获取用户或群组信息")

            # 设置当前机器人ID
            self.command_handler.set_current_bot_id(self._current_bot_id)

            return self.run_async(self.command_handler._show_user_stats_html(user_id, group_id))

        except Exception as e:
            self.logger.error(f"游戏信息命令处理失败: {e}")
            return MessageBuilder.text("❌ 命令处理失败，请稍后重试")

    def handle_game_ranking(self, args):
        """处理游戏排行榜命令"""
        try:
            user_id, group_id = self.get_user_group_from_message(self._current_message_data)
            if not user_id or not group_id:
                return MessageBuilder.text("❌ 无法获取用户或群组信息")

            # 设置当前机器人ID
            self.command_handler.set_current_bot_id(self._current_bot_id)

            return self.run_async(self.command_handler._show_ranking_html(group_id, []))

        except Exception as e:
            self.logger.error(f"游戏排行榜命令处理失败: {e}")
            return MessageBuilder.text("❌ 命令处理失败，请稍后重试")

    # ==================== Hook事件处理器 ====================

    def handle_message_hook(self, message_data, user_id=None, bot_id=None):
        """处理消息Hook"""
        try:
            # 保存当前消息数据和bot_id
            self._current_message_data = message_data
            self._current_bot_id = bot_id

            content = message_data.get('content', '').strip()

            # 处理命令
            result = self._handle_command(content, bot_id)
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error(bot_id or 0, f"棋类游戏插件处理消息异常: {e}", "CHESS_GAMES_HOOK_ERROR")
            return {'handled': False}

    def _handle_command(self, content, bot_id):
        """处理命令的内部方法"""

        # 移除开头的斜杠（如果有）
        if content.startswith('/'):
            content = content[1:]

        # 分割命令和参数
        parts = content.split()
        if not parts:
            return {'handled': False}

        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # 检查是否是支持的命令
        if command in self.command_handlers:
            try:
                response = self.command_handlers[command](args)

                # 检查是否是多消息响应
                if isinstance(response, list):
                    return {
                        'response': response,
                        'handled': True
                    }
                else:
                    return {
                        'response': response,
                        'handled': True
                    }
            except Exception as e:
                import traceback
                traceback.print_exc()
                log_error(bot_id or 0, f"棋类游戏插件命令处理异常: {e}", "CHESS_GAMES_COMMAND_ERROR")
                return {
                    'response': MessageBuilder.text("❌ 命令处理失败，请稍后重试"),
                    'handled': True
                }
        else:
            pass

        return {'handled': False}

    def on_bot_start_hook(self, bot_id):
        """机器人启动Hook"""
        self.logger.info(f"棋类游戏插件已为机器人 {bot_id} 准备就绪")
        return {'message': f'棋类游戏插件已为机器人 {bot_id} 准备就绪'}

    def on_bot_stop_hook(self, bot_id):
        """机器人停止Hook"""
        # 清理该机器人的活跃游戏
        self.game_manager.cleanup_bot_games(bot_id)
        self.logger.info(f"棋类游戏插件已为机器人 {bot_id} 清理资源")
        return {'message': f'棋类游戏插件已为机器人 {bot_id} 清理资源'}

    # ==================== 插件生命周期 ====================

    def on_enable(self):
        """插件启用时调用"""
        super().on_enable()
        self.logger.info("棋类游戏插件已启用，支持井字棋和五子棋游戏")

    def on_disable(self):
        """插件禁用时调用"""
        super().on_disable()
        # 清理所有活跃游戏
        self.game_manager.cleanup_all_games()
        self.logger.info("棋类游戏插件已禁用")

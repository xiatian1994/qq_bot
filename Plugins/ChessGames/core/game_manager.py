"""
游戏状态管理器
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any


class GameSession:
    """游戏会话类"""

    def __init__(self, game_id: str, game_type: str, player1_id: str,
                 player2_id: str, group_id: str, bot_id: int):
        self.game_id = game_id
        self.game_type = game_type  # 'tictactoe' or 'gomoku'
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.group_id = group_id
        self.bot_id = bot_id
        self.current_player = player1_id  # 当前轮到的玩家
        self.start_time = datetime.utcnow()
        self.last_move_time = datetime.utcnow()
        self.moves_count = 0
        self.game_state = None  # 具体的游戏状态对象
        self.is_finished = False
        self.winner_id = None
        self.is_ai_game = player2_id == 'AI'

    def switch_player(self):
        """切换当前玩家"""
        if self.current_player == self.player1_id:
            self.current_player = self.player2_id
        else:
            self.current_player = self.player1_id
        self.last_move_time = datetime.utcnow()

    def is_player_turn(self, player_id: str) -> bool:
        """检查是否轮到指定玩家"""
        return self.current_player == player_id

    def is_player_in_game(self, player_id: str) -> bool:
        """检查玩家是否在游戏中"""
        return player_id in [self.player1_id, self.player2_id]

    def is_timeout(self, timeout_minutes: int = 10) -> bool:
        """检查游戏是否超时"""
        return datetime.utcnow() - self.last_move_time > timedelta(minutes=timeout_minutes)

    def get_opponent(self, player_id: str) -> Optional[str]:
        """获取对手ID"""
        if player_id == self.player1_id:
            return self.player2_id
        elif player_id == self.player2_id:
            return self.player1_id
        return None

    def finish_game(self, winner_id: Optional[str] = None):
        """结束游戏"""
        self.is_finished = True
        self.winner_id = winner_id

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'game_id': self.game_id,
            'game_type': self.game_type,
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'group_id': self.group_id,
            'bot_id': self.bot_id,
            'current_player': self.current_player,
            'start_time': self.start_time.isoformat(),
            'last_move_time': self.last_move_time.isoformat(),
            'moves_count': self.moves_count,
            'is_finished': self.is_finished,
            'winner_id': self.winner_id,
            'is_ai_game': self.is_ai_game
        }


class GameManager:
    """游戏状态管理器"""

    def __init__(self):
        # 活跃游戏会话 {game_id: GameSession}
        self.active_games: Dict[str, GameSession] = {}

        # 用户游戏映射 {user_id: game_id}
        self.user_games: Dict[str, str] = {}

        # 群组游戏映射 {group_id: [game_id1, game_id2, ...]}
        self.group_games: Dict[str, List[str]] = {}

        # 机器人游戏映射 {bot_id: [game_id1, game_id2, ...]}
        self.bot_games: Dict[int, List[str]] = {}

        # 等待匹配的玩家 {group_id: {game_type: [(user_id, timestamp), ...]}}
        self.waiting_players: Dict[str, Dict[str, List[tuple]]] = {}

    def generate_game_id(self, game_type: str, player1_id: str, group_id: str) -> str:
        """生成游戏ID"""
        timestamp = int(time.time())
        return f"{game_type}_{group_id}_{player1_id}_{timestamp}"

    def create_game(self, game_type: str, player1_id: str, player2_id: str,
                    group_id: str, bot_id: int) -> GameSession:
        """创建新游戏"""
        # 检查玩家是否已经在其他游戏中
        if player1_id in self.user_games:
            raise Exception("玩家1已经在其他游戏中")
        if player2_id != 'AI' and player2_id in self.user_games:
            raise Exception("玩家2已经在其他游戏中")

        # 生成游戏ID
        game_id = self.generate_game_id(game_type, player1_id, group_id)

        # 创建游戏会话
        session = GameSession(game_id, game_type, player1_id, player2_id, group_id, bot_id)

        # 添加到各种映射中
        self.active_games[game_id] = session
        self.user_games[player1_id] = game_id
        if player2_id != 'AI':
            self.user_games[player2_id] = game_id

        # 添加到群组游戏列表
        if group_id not in self.group_games:
            self.group_games[group_id] = []
        self.group_games[group_id].append(game_id)

        # 添加到机器人游戏列表
        if bot_id not in self.bot_games:
            self.bot_games[bot_id] = []
        self.bot_games[bot_id].append(game_id)

        return session

    def get_game(self, game_id: str) -> Optional[GameSession]:
        """获取游戏会话"""
        return self.active_games.get(game_id)

    def get_user_game(self, user_id: str, group_id: str = None) -> Optional[GameSession]:
        """获取用户当前的游戏"""
        # 如果指定了群组，查找该用户在该群组中的游戏
        if group_id:
            for game_id, game in self.active_games.items():
                if (game.group_id == group_id and
                        game.is_player_in_game(user_id) and
                        not game.is_finished):
                    return game
            return None

        # 如果没有指定群组，使用原来的逻辑（向后兼容）
        game_id = self.user_games.get(user_id)
        if game_id:
            return self.active_games.get(game_id)
        return None

    def get_group_games(self, group_id: str) -> List[GameSession]:
        """获取群组中的所有活跃游戏"""
        game_ids = self.group_games.get(group_id, [])
        return [self.active_games[game_id] for game_id in game_ids if game_id in self.active_games]

    def add_waiting_player(self, user_id: str, group_id: str, game_type: str, timeout_minutes: int = 1) -> Optional[
        str]:
        """添加等待匹配的玩家，如果找到匹配则返回对手ID"""
        current_time = time.time()

        if group_id not in self.waiting_players:
            self.waiting_players[group_id] = {}

        if game_type not in self.waiting_players[group_id]:
            self.waiting_players[group_id][game_type] = []

        waiting_list = self.waiting_players[group_id][game_type]

        # 清理超时的等待玩家
        self._cleanup_expired_waiting_players(group_id, game_type, timeout_minutes)

        # 检查是否已经在等待列表中
        for waiting_user, _ in waiting_list:
            if waiting_user == user_id:
                return None

        # 如果有其他玩家在等待，进行匹配
        if waiting_list:
            opponent_id, _ = waiting_list.pop(0)  # 取出第一个等待的玩家
            # 清理空列表
            if not waiting_list:
                del self.waiting_players[group_id][game_type]
                if not self.waiting_players[group_id]:
                    del self.waiting_players[group_id]
            return opponent_id
        else:
            # 没有等待的玩家，加入等待列表
            waiting_list.append((user_id, current_time))
            return None

    def _cleanup_expired_waiting_players(self, group_id: str, game_type: str, timeout_minutes: int):
        """清理超时的等待玩家"""
        if (group_id not in self.waiting_players or
                game_type not in self.waiting_players[group_id]):
            return

        current_time = time.time()
        timeout_seconds = timeout_minutes * 60
        waiting_list = self.waiting_players[group_id][game_type]

        # 过滤掉超时的玩家
        valid_players = [(user_id, timestamp) for user_id, timestamp in waiting_list
                         if current_time - timestamp < timeout_seconds]

        if len(valid_players) != len(waiting_list):
            # 有玩家超时，更新列表
            if valid_players:
                self.waiting_players[group_id][game_type] = valid_players
            else:
                # 所有玩家都超时，删除列表
                del self.waiting_players[group_id][game_type]
                if not self.waiting_players[group_id]:
                    del self.waiting_players[group_id]

    def remove_waiting_player(self, user_id: str, group_id: str, game_type: str) -> bool:
        """移除等待匹配的玩家"""
        if (group_id in self.waiting_players and
                game_type in self.waiting_players[group_id]):

            waiting_list = self.waiting_players[group_id][game_type]
            for i, (waiting_user, _) in enumerate(waiting_list):
                if waiting_user == user_id:
                    waiting_list.pop(i)

                    # 清理空列表
                    if not waiting_list:
                        del self.waiting_players[group_id][game_type]
                        if not self.waiting_players[group_id]:
                            del self.waiting_players[group_id]
                    return True
        return False

    def get_waiting_players(self, group_id: str, game_type: str) -> List[str]:
        """获取等待匹配的玩家列表"""
        if (group_id in self.waiting_players and
                game_type in self.waiting_players[group_id]):
            # 先清理超时玩家
            self._cleanup_expired_waiting_players(group_id, game_type, 1)
            # 返回用户ID列表
            if (group_id in self.waiting_players and
                    game_type in self.waiting_players[group_id]):
                return [user_id for user_id, _ in self.waiting_players[group_id][game_type]]
        return []

    def get_waiting_time(self, user_id: str, group_id: str, game_type: str) -> Optional[int]:
        """获取用户等待时间（秒）"""
        if (group_id in self.waiting_players and
                game_type in self.waiting_players[group_id]):

            current_time = time.time()
            for waiting_user, timestamp in self.waiting_players[group_id][game_type]:
                if waiting_user == user_id:
                    return int(current_time - timestamp)
        return None

    def remove_game(self, game_id: str) -> bool:
        """移除游戏"""
        if game_id not in self.active_games:
            return False

        session = self.active_games[game_id]

        # 从用户游戏映射中移除
        if session.player1_id in self.user_games:
            del self.user_games[session.player1_id]
        if session.player2_id != 'AI' and session.player2_id in self.user_games:
            del self.user_games[session.player2_id]

        # 从群组游戏列表中移除
        if session.group_id in self.group_games:
            if game_id in self.group_games[session.group_id]:
                self.group_games[session.group_id].remove(game_id)
            if not self.group_games[session.group_id]:
                del self.group_games[session.group_id]

        # 从机器人游戏列表中移除
        if session.bot_id in self.bot_games:
            if game_id in self.bot_games[session.bot_id]:
                self.bot_games[session.bot_id].remove(game_id)
            if not self.bot_games[session.bot_id]:
                del self.bot_games[session.bot_id]

        # 从活跃游戏中移除
        del self.active_games[game_id]
        return True

    def cleanup_timeout_games(self, timeout_minutes: int = 10) -> List[str]:
        """清理超时的游戏"""
        timeout_games = []

        for game_id, session in list(self.active_games.items()):
            if session.is_timeout(timeout_minutes):
                timeout_games.append(game_id)
                self.remove_game(game_id)

        return timeout_games

    def cleanup_bot_games(self, bot_id: int) -> int:
        """清理指定机器人的所有游戏"""
        if bot_id not in self.bot_games:
            return 0

        game_ids = self.bot_games[bot_id].copy()
        count = 0

        for game_id in game_ids:
            if self.remove_game(game_id):
                count += 1

        return count

    def cleanup_all_games(self) -> int:
        """清理所有游戏"""
        count = len(self.active_games)
        self.active_games.clear()
        self.user_games.clear()
        self.group_games.clear()
        self.bot_games.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            'active_games_count': len(self.active_games),
            'active_users_count': len(self.user_games),
            'active_groups_count': len(self.group_games),
            'active_bots_count': len(self.bot_games),
            'game_types': {
                'tictactoe': len([g for g in self.active_games.values() if g.game_type == 'tictactoe']),
                'gomoku': len([g for g in self.active_games.values() if g.game_type == 'gomoku'])
            },
            'ai_games_count': len([g for g in self.active_games.values() if g.is_ai_game])
        }

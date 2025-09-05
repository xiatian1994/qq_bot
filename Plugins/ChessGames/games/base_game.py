"""
游戏基类
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List, Dict, Any


class GameResult(Enum):
    """游戏结果枚举"""
    CONTINUE = "continue"  # 游戏继续
    WIN = "win"  # 有玩家获胜
    DRAW = "draw"  # 平局
    INVALID = "invalid"  # 无效移动


class MoveResult:
    """移动结果类"""

    def __init__(self, result: GameResult, winner: Optional[str] = None,
                 message: str = "", board_changed: bool = True):
        self.result = result
        self.winner = winner
        self.message = message
        self.board_changed = board_changed


class BaseGame(ABC):
    """游戏基类"""

    def __init__(self, player1_id: str, player2_id: str):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.current_player = player1_id
        self.moves_count = 0
        self.is_finished = False
        self.winner = None

    @abstractmethod
    def make_move(self, player_id: str, move: Any) -> MoveResult:
        """执行移动"""
        pass

    @abstractmethod
    def is_valid_move(self, move: Any) -> bool:
        """检查移动是否有效"""
        pass

    @abstractmethod
    def get_board_state(self) -> Any:
        """获取棋盘状态"""
        pass

    @abstractmethod
    def get_available_moves(self) -> List[Any]:
        """获取可用的移动"""
        pass

    @abstractmethod
    def get_board_display(self) -> str:
        """获取棋盘的文本显示"""
        pass

    @abstractmethod
    def clone(self) -> 'BaseGame':
        """克隆游戏状态"""
        pass

    def switch_player(self):
        """切换当前玩家"""
        if self.current_player == self.player1_id:
            self.current_player = self.player2_id
        else:
            self.current_player = self.player1_id

    def is_player_turn(self, player_id: str) -> bool:
        """检查是否轮到指定玩家"""
        return self.current_player == player_id and not self.is_finished

    def get_opponent(self, player_id: str) -> Optional[str]:
        """获取对手ID"""
        if player_id == self.player1_id:
            return self.player2_id
        elif player_id == self.player2_id:
            return self.player1_id
        return None

    def finish_game(self, winner: Optional[str] = None):
        """结束游戏"""
        self.is_finished = True
        self.winner = winner

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于序列化）"""
        return {
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'current_player': self.current_player,
            'moves_count': self.moves_count,
            'is_finished': self.is_finished,
            'winner': self.winner,
            'board_state': self.get_board_state()
        }

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseGame':
        """从字典创建游戏实例（用于反序列化）"""
        pass

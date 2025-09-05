"""
井字棋游戏实现
"""

from typing import List, Optional, Dict, Any, Tuple

from .base_game import BaseGame, GameResult, MoveResult


class TicTacToe(BaseGame):
    """井字棋游戏类"""

    def __init__(self, player1_id: str, player2_id: str):
        super().__init__(player1_id, player2_id)
        # 3x3棋盘，0=空，1=玩家1(X)，2=玩家2(O)
        self.board = [[0 for _ in range(3)] for _ in range(3)]
        self.player_symbols = {player1_id: 'X', player2_id: 'O'}
        self.player_numbers = {player1_id: 1, player2_id: 2}

    def make_move(self, player_id: str, move: int) -> MoveResult:
        """执行移动
        
        Args:
            player_id: 玩家ID
            move: 移动位置 (1-9)
        """
        if self.is_finished:
            return MoveResult(GameResult.INVALID, message="\n❌ 游戏已结束")

        if not self.is_player_turn(player_id):
            return MoveResult(GameResult.INVALID, message="\n❌ 不是您的回合")

        if not self.is_valid_move(move):
            return MoveResult(GameResult.INVALID, message="\n❌ 无效的移动位置")

        # 转换位置 (1-9 -> row, col)
        row, col = self._position_to_coords(move)

        # 执行移动
        self.board[row][col] = self.player_numbers[player_id]
        self.moves_count += 1

        # 检查游戏结果
        winner = self._check_winner()
        if winner:
            self.finish_game(winner)
            symbol = self.player_symbols[winner]
            return MoveResult(GameResult.WIN, winner, f"\n🎉 玩家 {symbol} 获胜！")
        elif self._is_board_full():
            self.finish_game()
            return MoveResult(GameResult.DRAW, message="\n🤝 平局！")
        else:
            self.switch_player()
            next_symbol = self.player_symbols[self.current_player]
            return MoveResult(GameResult.CONTINUE, message=f"\n轮到玩家 {next_symbol} 下棋")

    def is_valid_move(self, move: int) -> bool:
        """检查移动是否有效"""
        if not isinstance(move, int) or move < 1 or move > 9:
            return False

        row, col = self._position_to_coords(move)
        return self.board[row][col] == 0

    def get_board_state(self) -> List[List[int]]:
        """获取棋盘状态"""
        return [row[:] for row in self.board]

    def get_available_moves(self) -> List[int]:
        """获取可用的移动位置"""
        moves = []
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == 0:
                    moves.append(self._coords_to_position(i, j))
        return moves

    def get_board_display(self) -> str:
        """获取棋盘的文本显示"""
        symbols = {0: '⬜', 1: '❌', 2: '⭕'}

        display = "```\n井字棋棋盘：\n\n"
        display += "   1   2   3\n"

        for i in range(3):
            display += f"{chr(65 + i)}  "
            for j in range(3):
                display += f"{symbols[self.board[i][j]]}  "
            display += f"  {chr(65 + i)}\n"

        display += "   1   2   3\n\n"

        # 添加位置说明
        display += "位置编号：\n"
        display += "1 2 3\n4 5 6\n7 8 9\n"
        display += "```"

        return display

    def get_simple_display(self) -> str:
        """获取简单的棋盘显示（用于快速查看）"""
        symbols = {0: '·', 1: 'X', 2: 'O'}

        lines = []
        for i in range(3):
            line = ""
            for j in range(3):
                line += symbols[self.board[i][j]]
                if j < 2:
                    line += "|"
            lines.append(line)

        return "\n".join(lines)

    def clone(self) -> 'TicTacToe':
        """克隆游戏状态"""
        new_game = TicTacToe(self.player1_id, self.player2_id)
        new_game.board = [row[:] for row in self.board]
        new_game.current_player = self.current_player
        new_game.moves_count = self.moves_count
        new_game.is_finished = self.is_finished
        new_game.winner = self.winner
        return new_game

    def _position_to_coords(self, position: int) -> Tuple[int, int]:
        """将位置编号(1-9)转换为坐标(row, col)"""
        position -= 1  # 转换为0-8
        return position // 3, position % 3

    def _coords_to_position(self, row: int, col: int) -> int:
        """将坐标(row, col)转换为位置编号(1-9)"""
        return row * 3 + col + 1

    def _check_winner(self) -> Optional[str]:
        """检查是否有获胜者"""
        # 检查行
        for i in range(3):
            if self.board[i][0] != 0 and self.board[i][0] == self.board[i][1] == self.board[i][2]:
                return self._get_player_by_number(self.board[i][0])

        # 检查列
        for j in range(3):
            if self.board[0][j] != 0 and self.board[0][j] == self.board[1][j] == self.board[2][j]:
                return self._get_player_by_number(self.board[0][j])

        # 检查对角线
        if self.board[0][0] != 0 and self.board[0][0] == self.board[1][1] == self.board[2][2]:
            return self._get_player_by_number(self.board[0][0])

        if self.board[0][2] != 0 and self.board[0][2] == self.board[1][1] == self.board[2][0]:
            return self._get_player_by_number(self.board[0][2])

        return None

    def _is_board_full(self) -> bool:
        """检查棋盘是否已满"""
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == 0:
                    return False
        return True

    def _get_player_by_number(self, number: int) -> Optional[str]:
        """根据玩家编号获取玩家ID"""
        for player_id, player_number in self.player_numbers.items():
            if player_number == number:
                return player_id
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = super().to_dict()
        data.update({
            'game_type': 'tictactoe',
            'board': self.board,
            'player_symbols': self.player_symbols,
            'player_numbers': self.player_numbers
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TicTacToe':
        """从字典创建游戏实例"""
        game = cls(data['player1_id'], data['player2_id'])
        game.board = data['board']
        game.current_player = data['current_player']
        game.moves_count = data['moves_count']
        game.is_finished = data['is_finished']
        game.winner = data['winner']
        game.player_symbols = data['player_symbols']
        game.player_numbers = data['player_numbers']
        return game

    def get_game_info(self) -> Dict[str, Any]:
        """获取游戏信息"""
        return {
            'game_type': 'tictactoe',
            'game_name': '井字棋',
            'board_size': '3x3',
            'players': {
                self.player1_id: {'symbol': 'X', 'name': '玩家X'},
                self.player2_id: {'symbol': 'O', 'name': '玩家O'}
            },
            'current_player': self.current_player,
            'moves_count': self.moves_count,
            'is_finished': self.is_finished,
            'winner': self.winner,
            'available_moves': self.get_available_moves() if not self.is_finished else []
        }

    def get_html_data(self) -> Dict[str, Any]:
        """获取HTML模板渲染数据"""
        # 确定获胜者名称
        winner_name = None
        if self.winner:
            if self.winner == self.player1_id:
                winner_name = f"玩家X ({self.player1_id[-4:]})" if self.player2_id != 'AI' else "您"
            else:
                winner_name = f"玩家O ({self.player2_id[-4:]})" if self.player2_id != 'AI' else "AI"

        # 准备玩家名称
        player1_name = f"用户{self.player1_id[-4:]}" if self.player2_id != 'AI' else "您"
        player2_name = f"用户{self.player2_id[-4:]}" if self.player2_id != 'AI' else "AI"

        return {
            'board': self.board,
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'player1_name': player1_name,
            'player2_name': player2_name,
            'current_player': self.current_player,
            'moves_count': self.moves_count,
            'is_finished': self.is_finished,
            'winner': self.winner,
            'winner_name': winner_name,
            'game_duration': '进行中'  # 可以后续添加时间计算
        }

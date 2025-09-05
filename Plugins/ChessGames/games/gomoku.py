"""
五子棋游戏实现
"""

from typing import List, Optional, Dict, Any, Tuple

from .base_game import BaseGame, GameResult, MoveResult


class Gomoku(BaseGame):
    """五子棋游戏类"""

    def __init__(self, player1_id: str, player2_id: str, board_size: int = 15):
        super().__init__(player1_id, player2_id)
        self.board_size = board_size
        # 棋盘，0=空，1=玩家1(黑)，2=玩家2(白)
        self.board = [[0 for _ in range(board_size)] for _ in range(board_size)]
        self.player_symbols = {player1_id: '●', player2_id: '○'}
        self.player_numbers = {player1_id: 1, player2_id: 2}
        self.player_colors = {player1_id: '黑', player2_id: '白'}
        self.last_move = None  # 记录最后一步

    def make_move(self, player_id: str, move: str) -> MoveResult:
        """执行移动
        
        Args:
            player_id: 玩家ID
            move: 移动位置，格式如 "H8" (列行)
        """
        if self.is_finished:
            return MoveResult(GameResult.INVALID, message="\n❌ 游戏已结束")

        if not self.is_player_turn(player_id):
            return MoveResult(GameResult.INVALID, message="\n❌ 不是您的回合")

        # 解析移动位置
        coords = self._parse_move(move)
        if not coords:
            return MoveResult(GameResult.INVALID, message="\n❌ 无效的位置格式，请使用如 H8 的格式")

        row, col = coords
        if not self.is_valid_move((row, col)):
            return MoveResult(GameResult.INVALID, message="\n❌ 该位置已被占用或超出棋盘范围")

        # 执行移动
        self.board[row][col] = self.player_numbers[player_id]
        self.moves_count += 1
        self.last_move = (row, col)

        # 检查游戏结果
        if self._check_winner(row, col):
            self.finish_game(player_id)
            color = self.player_colors[player_id]
            return MoveResult(GameResult.WIN, player_id, f"\n🎉 {color}棋获胜！")
        elif self._is_board_full():
            self.finish_game()
            return MoveResult(GameResult.DRAW, message="\n🤝 平局！棋盘已满")
        else:
            self.switch_player()
            next_color = self.player_colors[self.current_player]
            return MoveResult(GameResult.CONTINUE, message=f"\n轮到{next_color}棋下棋")

    def is_valid_move(self, move: Tuple[int, int]) -> bool:
        """检查移动是否有效"""
        row, col = move
        if row < 0 or row >= self.board_size or col < 0 or col >= self.board_size:
            return False
        return self.board[row][col] == 0

    def get_board_state(self) -> List[List[int]]:
        """获取棋盘状态"""
        return [row[:] for row in self.board]

    def get_available_moves(self) -> List[Tuple[int, int]]:
        """获取可用的移动位置"""
        moves = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 0:
                    moves.append((i, j))
        return moves

    def get_board_display(self) -> str:
        """获取棋盘的文本显示"""
        symbols = {0: '·', 1: '●', 2: '○'}

        display = "```\n五子棋棋盘：\n\n"

        # 列标题
        display += "   "
        for j in range(self.board_size):
            display += f"{chr(65 + j)} "
        display += "\n"

        # 棋盘内容
        for i in range(self.board_size):
            display += f"{i + 1:2d} "
            for j in range(self.board_size):
                symbol = symbols[self.board[i][j]]
                # 标记最后一步
                if self.last_move and self.last_move == (i, j):
                    if self.board[i][j] == 1:
                        symbol = '⚫'
                    elif self.board[i][j] == 2:
                        symbol = '⚪'
                display += f"{symbol} "
            display += f"{i + 1:2d}\n"

        # 底部列标题
        display += "   "
        for j in range(self.board_size):
            display += f"{chr(65 + j)} "
        display += "\n```"

        return display

    def clone(self) -> 'Gomoku':
        """克隆游戏状态"""
        new_game = Gomoku(self.player1_id, self.player2_id, self.board_size)
        new_game.board = [row[:] for row in self.board]
        new_game.current_player = self.current_player
        new_game.moves_count = self.moves_count
        new_game.is_finished = self.is_finished
        new_game.winner = self.winner
        new_game.last_move = self.last_move
        return new_game

    def _parse_move(self, move: str) -> Optional[Tuple[int, int]]:
        """解析移动位置字符串，如 "H8" -> (7, 7)"""
        if not isinstance(move, str) or len(move) < 2:
            return None

        move = move.upper().strip()

        # 提取列字母和行数字
        col_char = move[0]
        row_str = move[1:]

        # 验证列字母
        if not col_char.isalpha() or ord(col_char) - ord('A') >= self.board_size:
            return None

        # 验证行数字
        try:
            row_num = int(row_str)
            if row_num < 1 or row_num > self.board_size:
                return None
        except ValueError:
            return None

        # 转换为数组索引 (0-based)
        col = ord(col_char) - ord('A')
        row = row_num - 1

        return (row, col)

    def _check_winner(self, row: int, col: int) -> bool:
        """检查在指定位置下棋后是否获胜"""
        winning_line = self._get_winning_line(row, col)
        return winning_line is not None

    def _get_winning_line(self, row: int, col: int) -> list:
        """获取获胜的五子连线位置"""
        player_num = self.board[row][col]

        # 四个方向：水平、垂直、对角线1、对角线2
        directions = [
            (0, 1),  # 水平
            (1, 0),  # 垂直
            (1, 1),  # 对角线1
            (1, -1)  # 对角线2
        ]

        for dr, dc in directions:
            positions = [(row, col)]  # 包含当前位置

            # 向一个方向检查
            r, c = row + dr, col + dc
            while (0 <= r < self.board_size and 0 <= c < self.board_size and
                   self.board[r][c] == player_num):
                positions.append((r, c))
                r, c = r + dr, c + dc

            # 向相反方向检查
            r, c = row - dr, col - dc
            while (0 <= r < self.board_size and 0 <= c < self.board_size and
                   self.board[r][c] == player_num):
                positions.insert(0, (r, c))  # 插入到开头保持顺序
                r, c = r - dr, c - dc

            # 如果连成5个或以上，返回获胜线位置
            if len(positions) >= 5:
                return positions[:5]  # 只返回前5个位置

        return None

    def _is_board_full(self) -> bool:
        """检查棋盘是否已满"""
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 0:
                    return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = super().to_dict()
        data.update({
            'game_type': 'gomoku',
            'board_size': self.board_size,
            'board': self.board,
            'player_symbols': self.player_symbols,
            'player_numbers': self.player_numbers,
            'player_colors': self.player_colors,
            'last_move': self.last_move
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Gomoku':
        """从字典创建游戏实例"""
        game = cls(data['player1_id'], data['player2_id'], data.get('board_size', 15))
        game.board = data['board']
        game.current_player = data['current_player']
        game.moves_count = data['moves_count']
        game.is_finished = data['is_finished']
        game.winner = data['winner']
        game.player_symbols = data['player_symbols']
        game.player_numbers = data['player_numbers']
        game.player_colors = data['player_colors']
        game.last_move = data.get('last_move')
        return game

    def get_game_info(self) -> Dict[str, Any]:
        """获取游戏信息"""
        return {
            'game_type': 'gomoku',
            'game_name': '五子棋',
            'board_size': f'{self.board_size}x{self.board_size}',
            'players': {
                self.player1_id: {'symbol': '●', 'color': '黑', 'name': '黑棋'},
                self.player2_id: {'symbol': '○', 'color': '白', 'name': '白棋'}
            },
            'current_player': self.current_player,
            'moves_count': self.moves_count,
            'is_finished': self.is_finished,
            'winner': self.winner,
            'last_move': self.last_move,
            'available_moves_count': len(self.get_available_moves()) if not self.is_finished else 0
        }

    def get_html_data(self) -> Dict[str, Any]:
        """获取HTML模板渲染数据"""
        # 确定获胜者名称
        winner_name = None
        if self.winner:
            if self.winner == self.player1_id:
                winner_name = f"黑棋 ({self.player1_id[-4:]})" if self.player2_id != 'AI' else "您"
            else:
                winner_name = f"白棋 ({self.player2_id[-4:]})" if self.player2_id != 'AI' else "AI"

        # 准备玩家名称
        player1_name = f"用户{self.player1_id[-4:]}" if self.player2_id != 'AI' else "您"
        player2_name = f"用户{self.player2_id[-4:]}" if self.player2_id != 'AI' else "AI"

        # 获取获胜线信息
        winning_line = None
        if self.is_finished and self.winner and self.last_move:
            winning_line = self._get_winning_line(self.last_move[0], self.last_move[1])

        return {
            'board': self.board,
            'board_size': self.board_size,
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'player1_name': player1_name,
            'player2_name': player2_name,
            'current_player': self.current_player,
            'moves_count': self.moves_count,
            'is_finished': self.is_finished,
            'winner': self.winner,
            'winner_name': winner_name,
            'last_move': self.last_move,
            'winning_line': winning_line,
            'game_duration': '进行中'  # 可以后续添加时间计算
        }

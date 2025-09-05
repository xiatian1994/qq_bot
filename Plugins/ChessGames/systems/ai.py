"""
AI系统 - 提供不同难度的AI对手
"""

import random
from typing import List, Tuple, Optional, Any

from ..games.base_game import BaseGame
from ..games.gomoku import Gomoku
from ..games.tictactoe import TicTacToe


class AISystem:
    """AI系统"""

    def __init__(self):
        """初始化AI系统"""
        pass

    def get_ai_move(self, game: BaseGame, difficulty: str = 'medium') -> Optional[Any]:
        """
        获取AI的下一步移动

        Args:
            game: 游戏实例
            difficulty: 难度级别 ('easy', 'medium', 'hard')

        Returns:
            AI的移动，格式取决于游戏类型
        """
        if isinstance(game, TicTacToe):
            return self._get_tictactoe_move(game, difficulty)
        elif isinstance(game, Gomoku):
            return self._get_gomoku_move(game, difficulty)
        else:
            return None

    def _get_tictactoe_move(self, game: TicTacToe, difficulty: str) -> Optional[int]:
        """获取井字棋AI移动"""
        available_moves = game.get_available_moves()
        if not available_moves:
            return None

        if difficulty == 'easy':
            # 简单难度：随机选择
            return random.choice(available_moves)

        elif difficulty == 'medium':
            # 中等难度：优先考虑获胜和阻止对手获胜
            ai_player = 'AI'
            opponent = game.get_opponent(ai_player)

            # 检查是否能获胜
            for move in available_moves:
                test_game = game.clone()
                result = test_game.make_move(ai_player, move)
                if result.result.value == 'win':
                    return move

            # 检查是否需要阻止对手获胜
            for move in available_moves:
                test_game = game.clone()
                test_game.current_player = opponent
                result = test_game.make_move(opponent, move)
                if result.result.value == 'win':
                    return move

            # 优先选择中心和角落
            priority_moves = [5, 1, 3, 7, 9, 2, 4, 6, 8]
            for move in priority_moves:
                if move in available_moves:
                    return move

            return random.choice(available_moves)

        elif difficulty == 'hard':
            # 困难难度：使用Minimax算法
            return self._minimax_tictactoe(game, 'AI', 9)[1]

        return random.choice(available_moves)

    def _get_gomoku_move(self, game: Gomoku, difficulty: str) -> Optional[str]:
        """获取五子棋AI移动"""
        available_moves = game.get_available_moves()
        if not available_moves:
            return None

        if difficulty == 'easy':
            # 简单难度：随机选择
            row, col = random.choice(available_moves)
            return f"{chr(65 + col)}{row + 1}"

        elif difficulty == 'medium':
            # 中等难度：基本策略
            move = self._get_strategic_gomoku_move(game, available_moves)
            if move:
                row, col = move
                return f"{chr(65 + col)}{row + 1}"

            # 如果没有找到策略性移动，随机选择
            row, col = random.choice(available_moves)
            return f"{chr(65 + col)}{row + 1}"

        elif difficulty == 'hard':
            # 困难难度：更高级的策略
            move = self._get_advanced_gomoku_move(game, available_moves)
            if move:
                row, col = move
                return f"{chr(65 + col)}{row + 1}"

            row, col = random.choice(available_moves)
            return f"{chr(65 + col)}{row + 1}"

        row, col = random.choice(available_moves)
        return f"{chr(65 + col)}{row + 1}"

    def _minimax_tictactoe(self, game: TicTacToe, player: str, depth: int) -> Tuple[int, Optional[int]]:
        """井字棋Minimax算法"""
        available_moves = game.get_available_moves()

        if game.is_finished or depth == 0:
            return self._evaluate_tictactoe(game, 'AI'), None

        if player == 'AI':
            max_score = float('-inf')
            best_move = None
            for move in available_moves:
                test_game = game.clone()
                test_game.make_move(player, move)
                score, _ = self._minimax_tictactoe(test_game, game.get_opponent(player), depth - 1)
                if score > max_score:
                    max_score = score
                    best_move = move
            return max_score, best_move
        else:
            min_score = float('inf')
            best_move = None
            for move in available_moves:
                test_game = game.clone()
                test_game.make_move(player, move)
                score, _ = self._minimax_tictactoe(test_game, game.get_opponent(player), depth - 1)
                if score < min_score:
                    min_score = score
                    best_move = move
            return min_score, best_move

    def _evaluate_tictactoe(self, game: TicTacToe, ai_player: str) -> int:
        """评估井字棋局面"""
        if game.is_finished:
            if game.winner == ai_player:
                return 10
            elif game.winner is None:
                return 0
            else:
                return -10
        return 0

    def _get_strategic_gomoku_move(self, game: Gomoku, available_moves: List[Tuple[int, int]]) -> Optional[
        Tuple[int, int]]:
        """获取五子棋策略性移动"""
        ai_player = 'AI'
        opponent = game.get_opponent(ai_player)

        # 检查是否能获胜
        for row, col in available_moves:
            test_game = game.clone()
            test_game.board[row][col] = test_game.player_numbers[ai_player]
            if test_game._check_winner(row, col):
                return (row, col)

        # 检查是否需要阻止对手获胜
        for row, col in available_moves:
            test_game = game.clone()
            test_game.board[row][col] = test_game.player_numbers[opponent]
            if test_game._check_winner(row, col):
                return (row, col)

        # 如果是第一步，选择中心附近
        if game.moves_count == 0:
            center = game.board_size // 2
            return (center, center)

        # 选择靠近已有棋子的位置
        if game.last_move:
            last_row, last_col = game.last_move
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = last_row + dr, last_col + dc
                    if (new_row, new_col) in available_moves:
                        return (new_row, new_col)

        return None

    def _get_advanced_gomoku_move(self, game: Gomoku, available_moves: List[Tuple[int, int]]) -> Optional[
        Tuple[int, int]]:
        """获取五子棋高级策略移动"""
        # 这里可以实现更复杂的五子棋AI算法
        # 目前使用基本策略
        return self._get_strategic_gomoku_move(game, available_moves)

    def get_difficulty_description(self, difficulty: str) -> str:
        """获取难度描述"""
        descriptions = {
            'easy': '简单 - 随机下棋',
            'medium': '中等 - 基本策略',
            'hard': '困难 - 高级算法'
        }
        return descriptions.get(difficulty, '未知难度')

    def get_available_difficulties(self) -> List[str]:
        """获取可用的难度级别"""
        return ['easy', 'medium', 'hard']

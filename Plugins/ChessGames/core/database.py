"""
棋类游戏数据库管理模块
"""

import os
from datetime import datetime
from typing import Optional, List

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Index, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class GameRecord(Base):
    """游戏记录表"""
    __tablename__ = 'game_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_type = Column(String(20), nullable=False)  # tictactoe, gomoku
    player1_id = Column(String(64), nullable=False)  # 玩家1的union_openid
    player2_id = Column(String(64), nullable=False)  # 玩家2的union_openid或'AI'
    group_id = Column(String(64), nullable=False)  # 群组ID
    winner_id = Column(String(64))  # 获胜者ID，平局时为None
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    moves_count = Column(Integer, default=0)  # 总步数
    game_data = Column(Text)  # JSON格式的游戏数据
    is_ai_game = Column(Boolean, default=False)  # 是否为AI对战

    # 数据完整性约束
    __table_args__ = (
        # 检查约束：确保游戏类型有效
        CheckConstraint("game_type IN ('tictactoe', 'gomoku')", name='ck_game_type_valid'),

        # 检查约束：确保步数为非负数
        CheckConstraint('moves_count >= 0', name='ck_moves_count_positive'),

        # 性能索引
        Index('idx_game_group_time', 'group_id', 'start_time'),
        Index('idx_game_player1', 'player1_id', 'start_time'),
        Index('idx_game_player2', 'player2_id', 'start_time'),
        Index('idx_game_type_time', 'game_type', 'start_time'),
        Index('idx_game_winner', 'winner_id', 'start_time'),
    )


class UserStats(Base):
    """用户游戏统计表"""
    __tablename__ = 'user_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False)  # union_openid
    group_id = Column(String(64), nullable=False)  # 群组ID
    game_type = Column(String(20), nullable=False)  # 游戏类型
    total_games = Column(Integer, default=0)  # 总游戏数
    wins = Column(Integer, default=0)  # 胜利数
    losses = Column(Integer, default=0)  # 失败数
    draws = Column(Integer, default=0)  # 平局数
    best_streak = Column(Integer, default=0)  # 最佳连胜
    current_streak = Column(Integer, default=0)  # 当前连胜
    last_game_time = Column(DateTime)  # 最后游戏时间

    # 数据完整性约束
    __table_args__ = (
        # 唯一约束：每个用户在每个群组中每种游戏类型只能有一条统计记录
        Index('idx_user_stats_unique', 'user_id', 'group_id', 'game_type', unique=True),

        # 检查约束：确保统计数据为非负数
        CheckConstraint('total_games >= 0', name='ck_total_games_positive'),
        CheckConstraint('wins >= 0', name='ck_wins_positive'),
        CheckConstraint('losses >= 0', name='ck_losses_positive'),
        CheckConstraint('draws >= 0', name='ck_draws_positive'),
        CheckConstraint('best_streak >= 0', name='ck_best_streak_positive'),
        CheckConstraint('current_streak >= 0', name='ck_current_streak_positive'),

        # 检查约束：确保游戏类型有效
        CheckConstraint("game_type IN ('tictactoe', 'gomoku')", name='ck_stats_game_type_valid'),

        # 性能索引
        Index('idx_stats_user_group', 'user_id', 'group_id'),
        Index('idx_stats_game_type', 'game_type'),
        Index('idx_stats_wins_desc', 'wins'),
    )


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        # 数据库文件路径
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chess_games.db')

        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # 创建数据库引擎
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)

        # 创建会话工厂
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_database(self):
        """初始化数据库"""
        try:
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            return True
        except Exception as e:
            raise Exception(f"数据库初始化失败: {e}")

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """关闭数据库会话"""
        try:
            session.close()
        except Exception:
            pass

    def save_game_record(self, game_type: str, player1_id: str, player2_id: str,
                         group_id: str, winner_id: Optional[str], moves_count: int,
                         game_data: str, is_ai_game: bool = False) -> bool:
        """保存游戏记录"""
        session = self.get_session()
        try:
            record = GameRecord(
                game_type=game_type,
                player1_id=player1_id,
                player2_id=player2_id,
                group_id=group_id,
                winner_id=winner_id,
                end_time=datetime.utcnow(),
                moves_count=moves_count,
                game_data=game_data,
                is_ai_game=is_ai_game
            )
            session.add(record)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise Exception(f"保存游戏记录失败: {e}")
        finally:
            self.close_session(session)

    def update_user_stats(self, user_id: str, group_id: str, game_type: str,
                          result: str) -> bool:
        """更新用户统计数据
        
        Args:
            user_id: 用户ID
            group_id: 群组ID  
            game_type: 游戏类型
            result: 游戏结果 ('win', 'loss', 'draw')
        """
        session = self.get_session()
        try:
            # 查找或创建用户统计记录
            stats = session.query(UserStats).filter(
                UserStats.user_id == user_id,
                UserStats.group_id == group_id,
                UserStats.game_type == game_type
            ).first()

            if not stats:
                stats = UserStats(
                    user_id=user_id,
                    group_id=group_id,
                    game_type=game_type
                )
                session.add(stats)

            # 确保字段不为None
            stats.total_games = (stats.total_games or 0) + 1
            stats.wins = stats.wins or 0
            stats.losses = stats.losses or 0
            stats.draws = stats.draws or 0
            stats.best_streak = stats.best_streak or 0
            stats.current_streak = stats.current_streak or 0
            stats.last_game_time = datetime.utcnow()

            if result == 'win':
                stats.wins += 1
                stats.current_streak += 1
                stats.best_streak = max(stats.best_streak, stats.current_streak)
            elif result == 'loss':
                stats.losses += 1
                stats.current_streak = 0
            elif result == 'draw':
                stats.draws += 1
                # 平局不影响连胜

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise Exception(f"更新用户统计失败: {e}")
        finally:
            self.close_session(session)

    def get_user_stats(self, user_id: str, group_id: str, game_type: str) -> Optional[UserStats]:
        """获取用户统计数据"""
        session = self.get_session()
        try:
            stats = session.query(UserStats).filter(
                UserStats.user_id == user_id,
                UserStats.group_id == group_id,
                UserStats.game_type == game_type
            ).first()
            return stats
        finally:
            self.close_session(session)

    def get_group_ranking(self, group_id: str, game_type: str, limit: int = 10) -> List[UserStats]:
        """获取群组排行榜"""
        session = self.get_session()
        try:
            rankings = session.query(UserStats).filter(
                UserStats.group_id == group_id,
                UserStats.game_type == game_type,
                UserStats.total_games > 0
            ).order_by(
                UserStats.wins.desc(),
                UserStats.total_games.desc()
            ).limit(limit).all()
            return rankings
        finally:
            self.close_session(session)

    def get_recent_games(self, group_id: str, limit: int = 10) -> List[GameRecord]:
        """获取最近的游戏记录"""
        session = self.get_session()
        try:
            games = session.query(GameRecord).filter(
                GameRecord.group_id == group_id
            ).order_by(
                GameRecord.start_time.desc()
            ).limit(limit).all()
            return games
        finally:
            self.close_session(session)

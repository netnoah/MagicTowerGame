"""
State Machine - 游戏状态机

管理游戏的不同状态和状态转换
"""

from typing import Callable, Dict, Optional, Any
from dataclasses import dataclass, field

from config import GameState


@dataclass
class StateTransition:
    """状态转换记录"""
    from_state: str
    to_state: str
    timestamp: float = 0.0


class GameStateMachine:
    """
    游戏状态机

    管理游戏状态的转换逻辑

    使用示例:
        sm = GameStateMachine()

        # 注册状态回调
        sm.on_enter(GameState.PLAYING, lambda: print("游戏开始"))
        sm.on_exit(GameState.PLAYING, lambda: print("暂停游戏"))

        # 切换状态
        sm.transition_to(GameState.PLAYING)

        # 检查当前状态
        if sm.is_state(GameState.PLAYING):
            # 游戏逻辑...
            pass
    """

    def __init__(self, initial_state: str = GameState.MENU):
        """
        初始化状态机

        Args:
            initial_state: 初始状态
        """
        self._current_state: str = initial_state
        self._previous_state: Optional[str] = None

        # 回调函数存储
        self._enter_callbacks: Dict[str, list[Callable]] = {}
        self._exit_callbacks: Dict[str, list[Callable]] = {}
        self._update_callbacks: Dict[str, Callable] = {}

        # 状态历史记录
        self._history: list[StateTransition] = []

    @property
    def current_state(self) -> str:
        """当前状态"""
        return self._current_state

    @property
    def previous_state(self) -> Optional[str]:
        """上一个状态"""
        return self._previous_state

    def is_state(self, state: str) -> bool:
        """检查是否处于指定状态"""
        return self._current_state == state

    def is_any_state(self, *states: str) -> bool:
        """检查是否处于任一指定状态"""
        return self._current_state in states

    def transition_to(self, new_state: str, timestamp: float = 0.0) -> bool:
        """
        转换到新状态

        Args:
            new_state: 目标状态
            timestamp: 时间戳（用于记录）

        Returns:
            是否成功转换
        """
        if new_state == self._current_state:
            return False

        # 执行退出回调
        self._execute_exit_callbacks(self._current_state)

        # 记录转换
        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state

        # 记录历史
        self._history.append(StateTransition(old_state, new_state, timestamp))
        if len(self._history) > 100:  # 限制历史记录长度
            self._history = self._history[-50:]

        # 执行进入回调
        self._execute_enter_callbacks(new_state)

        return True

    def go_back(self) -> bool:
        """返回上一个状态"""
        if self._previous_state is None:
            return False
        return self.transition_to(self._previous_state)

    def on_enter(self, state: str, callback: Callable) -> None:
        """
        注册状态进入回调

        Args:
            state: 状态名称
            callback: 回调函数
        """
        if state not in self._enter_callbacks:
            self._enter_callbacks[state] = []
        self._enter_callbacks[state].append(callback)

    def on_exit(self, state: str, callback: Callable) -> None:
        """
        注册状态退出回调

        Args:
            state: 状态名称
            callback: 回调函数
        """
        if state not in self._exit_callbacks:
            self._exit_callbacks[state] = []
        self._exit_callbacks[state].append(callback)

    def on_update(self, state: str, callback: Callable) -> None:
        """
        注册状态更新回调

        Args:
            state: 状态名称
            callback: 回调函数 (接收 delta_time 参数)
        """
        self._update_callbacks[state] = callback

    def update(self, delta_time: float) -> None:
        """
        更新当前状态

        Args:
            delta_time: 时间增量（秒）
        """
        if self._current_state in self._update_callbacks:
            self._update_callbacks[self._current_state](delta_time)

    def _execute_enter_callbacks(self, state: str) -> None:
        """执行状态进入回调"""
        if state in self._enter_callbacks:
            for callback in self._enter_callbacks[state]:
                callback()

    def _execute_exit_callbacks(self, state: str) -> None:
        """执行状态退出回调"""
        if state in self._exit_callbacks:
            for callback in self._exit_callbacks[state]:
                callback()

    def get_transition_count(self, from_state: str, to_state: str) -> int:
        """获取特定转换的次数"""
        return sum(
            1 for t in self._history
            if t.from_state == from_state and t.to_state == to_state
        )

    def clear_callbacks(self) -> None:
        """清除所有回调"""
        self._enter_callbacks.clear()
        self._exit_callbacks.clear()
        self._update_callbacks.clear()

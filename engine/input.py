"""
Input Handler - 输入处理

处理键盘和鼠标输入，支持按键映射和组合键
"""

from typing import Dict, Set, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import pygame
from pygame.key import ScancodeWrapper


class KeyAction(Enum):
    """按键动作类型"""
    PRESS = "press"      # 按下瞬间
    RELEASE = "release"  # 释放瞬间
    HOLD = "hold"        # 持续按住


@dataclass
class KeyBinding:
    """按键绑定"""
    key: int                    # pygame key constant
    action: KeyAction           # 动作类型
    callback: Callable[[], None]  # 回调函数
    name: str = ""              # 绑定名称（用于调试）

@dataclass
class CharBinding:
    """字符输入绑定（TEXTINPUT）"""
    char: str
    action: KeyAction
    callback: Callable[[], None]
    name: str = ""

@dataclass
class ScancodeBinding:
    """扫描码绑定"""
    scancode: int
    action: KeyAction
    callback: Callable[[], None]
    name: str = ""


class InputHandler:
    """
    输入处理器

    集中管理所有输入事件

    使用示例:
        input_handler = InputHandler()

        # 绑定按键
        input_handler.bind_key(pygame.K_UP, KeyAction.PRESS, player.move_up, "move_up")
        input_handler.bind_key(pygame.K_ESCAPE, KeyAction.PRESS, game.pause, "pause")

        # 在游戏循环中处理
        for event in pygame.event.get():
            input_handler.handle_event(event)

        # 处理持续按键
        input_handler.update()
    """

    def __init__(self):
        # 按键绑定
        self._bindings: Dict[int, list[KeyBinding]] = {}
        # 字符输入绑定（TEXTINPUT）
        self._char_bindings: Dict[str, list[CharBinding]] = {}
        # 扫描码绑定
        self._scancode_bindings: Dict[int, list[ScancodeBinding]] = {}

        # 当前按下的键
        self._held_keys: Set[int] = set()
        self._held_scancodes: Set[int] = set()

        # 按键状态缓存（防止重复触发）
        self._press_handled: Set[int] = set()
        # 扫描码状态缓存（防止重复触发）
        self._scancode_press_handled: Set[int] = set()

        # 鼠标状态
        self._mouse_pos: tuple[int, int] = (0, 0)
        self._mouse_pressed: Dict[int, bool] = {1: False, 2: False, 3: False}

        # 是否启用
        self._enabled: bool = True

    def bind_key(self, key: int, action: KeyAction,
                callback: Callable[[], None], name: str = "") -> None:
        """
        绑定按键回调

        Args:
            key: pygame key constant (如 pygame.K_UP)
            action: KeyAction 类型
            callback: 回调函数
            name: 绑定名称（可选）
        """
        binding = KeyBinding(key=key, action=action, callback=callback, name=name)

        if key not in self._bindings:
            self._bindings[key] = []
        self._bindings[key].append(binding)

    def unbind_key(self, key: int, action: Optional[KeyAction] = None) -> None:
        """
        解绑按键

        Args:
            key: 要解绑的键
            action: 要解绑的动作类型（None 表示解绑所有）
        """
        if key not in self._bindings:
            return

        if action is None:
            del self._bindings[key]
        else:
            self._bindings[key] = [
                b for b in self._bindings[key] if b.action != action
            ]

    def bind_char(self, char: str, action: KeyAction,
                  callback: Callable[[], None], name: str = "") -> None:
        """
        绑定字符输入（TEXTINPUT）
        """
        c = (char or "").lower()
        if not c:
            return
        binding = CharBinding(char=c, action=action, callback=callback, name=name)
        if c not in self._char_bindings:
            self._char_bindings[c] = []
        self._char_bindings[c].append(binding)

    def unbind_char(self, char: str, action: Optional[KeyAction] = None) -> None:
        """
        解绑字符输入
        """
        c = (char or "").lower()
        if not c or c not in self._char_bindings:
            return
        if action is None:
            del self._char_bindings[c]
        else:
            self._char_bindings[c] = [
                b for b in self._char_bindings[c] if b.action != action
            ]

    def bind_scancode(self, scancode: int, action: KeyAction,
                      callback: Callable[[], None], name: str = "") -> None:
        """绑定扫描码输入"""
        binding = ScancodeBinding(scancode=scancode, action=action, callback=callback, name=name)
        if scancode not in self._scancode_bindings:
            self._scancode_bindings[scancode] = []
        self._scancode_bindings[scancode].append(binding)

    def unbind_scancode(self, scancode: int, action: Optional[KeyAction] = None) -> None:
        """解绑扫描码输入"""
        if scancode not in self._scancode_bindings:
            return
        if action is None:
            del self._scancode_bindings[scancode]
        else:
            self._scancode_bindings[scancode] = [
                b for b in self._scancode_bindings[scancode] if b.action != action
            ]

    def unbind_all(self) -> None:
        """解绑所有按键、字符和扫描码"""
        self._bindings.clear()
        self._char_bindings.clear()
        self._scancode_bindings.clear()

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        处理 pygame 事件

        Args:
            event: pygame 事件对象
        """
        if event.type == pygame.KEYDOWN:
            if not self._enabled:
                return
            self._handle_key_press(event.key)
            sc = getattr(event, 'scancode', None)
            if sc is not None:
                self._handle_scancode_press(sc)

        elif event.type == pygame.KEYUP:
            self._handle_key_release(event.key)
            sc = getattr(event, 'scancode', None)
            if sc is not None:
                self._handle_scancode_release(sc)

        elif event.type == pygame.TEXTINPUT:
            if not self._enabled:
                return
            self._handle_text_input(getattr(event, 'text', ''))

        elif event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in self._mouse_pressed:
                self._mouse_pressed[event.button] = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in self._mouse_pressed:
                self._mouse_pressed[event.button] = False

    def update(self) -> None:
        """
        每帧更新，处理持续按键

        应该在游戏循环的主更新阶段调用
        """
        if not self._enabled:
            return

        # 处理持续按住的键
        for key in self._held_keys:
            self._trigger_bindings(key, KeyAction.HOLD)
        for sc in self._held_scancodes:
            self._trigger_scancode_bindings(sc, KeyAction.HOLD)

    def _handle_key_press(self, key: int) -> None:
        """处理按键按下"""
        if key in self._press_handled:
            return

        self._held_keys.add(key)
        self._press_handled.add(key)

        self._trigger_bindings(key, KeyAction.PRESS)

    def _handle_key_release(self, key: int) -> None:
        """处理按键释放"""
        self._held_keys.discard(key)
        self._press_handled.discard(key)
        self._trigger_bindings(key, KeyAction.RELEASE)

    def _handle_scancode_press(self, scancode: int) -> None:
        """处理扫描码按下"""
        if scancode in self._scancode_press_handled:
            return
        self._held_scancodes.add(scancode)
        self._scancode_press_handled.add(scancode)
        self._trigger_scancode_bindings(scancode, KeyAction.PRESS)

    def _handle_scancode_release(self, scancode: int) -> None:
        """处理扫描码释放"""
        self._held_scancodes.discard(scancode)
        self._scancode_press_handled.discard(scancode)
        self._trigger_scancode_bindings(scancode, KeyAction.RELEASE)

    def _handle_text_input(self, text: str) -> None:
        """处理文本输入（兼容中文输入法/IME）"""
        if not text:
            return
        for ch in text.lower():
            self._trigger_char_bindings(ch, KeyAction.PRESS)

    def _trigger_bindings(self, key: int, action: KeyAction) -> None:
        """触发指定键和动作的所有绑定"""
        if key not in self._bindings:
            return

        for binding in self._bindings[key]:
            if binding.action == action:
                binding.callback()

    def _trigger_char_bindings(self, char: str, action: KeyAction) -> None:
        """触发指定字符和动作的所有绑定（TEXTINPUT）"""
        if char not in self._char_bindings:
            return
        for binding in self._char_bindings[char]:
            if binding.action == action:
                binding.callback()

    def _trigger_scancode_bindings(self, scancode: int, action: KeyAction) -> None:
        """触发指定扫描码和动作的所有绑定"""
        if scancode not in self._scancode_bindings:
            return
        for binding in self._scancode_bindings[scancode]:
            if binding.action == action:
                binding.callback()

    def is_key_held(self, key: int) -> bool:
        """
        检查键是否被按住

        Args:
            key: pygame key constant

        Returns:
            是否正在被按住
        """
        return key in self._held_keys

    def is_key_pressed(self, key: int) -> bool:
        """
        检查键是否刚刚被按下（单次触发）

        Args:
            key: pygame key constant

        Returns:
            是否刚刚按下
        """
        return key in self._held_keys and key not in self._press_handled

    def get_mouse_pos(self) -> tuple[int, int]:
        """获取鼠标位置"""
        return self._mouse_pos

    def is_mouse_pressed(self, button: int = 1) -> bool:
        """
        检查鼠标按钮是否被按下

        Args:
            button: 鼠标按钮 (1=左, 2=中, 3=右)

        Returns:
            是否被按下
        """
        return self._mouse_pressed.get(button, False)

    def enable(self) -> None:
        """启用输入处理"""
        self._enabled = True

    def disable(self) -> None:
        """禁用输入处理"""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """是否启用"""
        return self._enabled

    def get_held_keys(self) -> Set[int]:
        """获取当前按住的所有键"""
        return self._held_keys.copy()


# ============================================================
# 预定义的按键映射
# ============================================================

def create_default_bindings(input_handler: InputHandler,
                            game: Any) -> None:
    """
    创建默认的按键绑定

    Args:
        input_handler: 输入处理器
        game: 游戏实例（需要有相应的方法）
    """
    # 移动 - 持续按住
    input_handler.bind_key(
        pygame.K_UP, KeyAction.HOLD,
        lambda: game.move_player("up"),
        "move_up"
    )
    input_handler.bind_key(
        pygame.K_DOWN, KeyAction.HOLD,
        lambda: game.move_player("down"),
        "move_down"
    )
    input_handler.bind_key(
        pygame.K_LEFT, KeyAction.HOLD,
        lambda: game.move_player("left"),
        "move_left"
    )
    input_handler.bind_key(
        pygame.K_RIGHT, KeyAction.HOLD,
        lambda: game.move_player("right"),
        "move_right"
    )

    # 暂停 - 单次按下
    input_handler.bind_key(
        pygame.K_ESCAPE, KeyAction.PRESS,
        game.toggle_pause,
        "pause"
    )

    # 确认/交互 - 单次按下
    input_handler.bind_key(
        pygame.K_RETURN, KeyAction.PRESS,
        game.confirm,
        "confirm"
    )
    input_handler.bind_key(
        pygame.K_SPACE, KeyAction.PRESS,
        game.confirm,
        "confirm_space"
    )

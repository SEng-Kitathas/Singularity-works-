from __future__ import annotations
# complexity_justified: OS window anchoring requires platform-specific branching and guarded Win32 interop.
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class WindowRect:
    left: int
    top: int
    right: int
    bottom: int
    @property
    def width(self) -> int:
        return max(0, self.right - self.left)
    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

@dataclass
class HUDAnchorPlan:
    target_title: str
    target_rect: WindowRect | None
    console_rect: WindowRect | None
    applied: bool = False
    centered_target: bool = False
    docked_console: bool = False
    dock_side: str = "right"
    note: str = ""


def _windows_api():
    try:
        import win32con, win32gui, win32console  # type: ignore
        return win32con, win32gui, win32console
    except Exception:
        return None


def _work_area() -> WindowRect | None:
    api = _windows_api()
    if api is None:
        return None
    win32con, win32gui, _ = api
    try:
        SPI_GETWORKAREA = 48
        rect = win32gui.SystemParametersInfo(SPI_GETWORKAREA)
        return WindowRect(*rect)
    except Exception:
        return None


def _find_window(title_substring: str):
    api = _windows_api()
    if api is None:
        return None
    _, win32gui, _ = api
    matches: list[int] = []
    needle = title_substring.lower()
    def cb(hwnd, _extra):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd) or ""
            if needle in title.lower():
                matches.append(hwnd)
        except Exception:
            return
    win32gui.EnumWindows(cb, None)
    return matches[0] if matches else None


def _get_rect(hwnd: int) -> WindowRect | None:
    api = _windows_api()
    if api is None:
        return None
    _, win32gui, _ = api
    try:
        return WindowRect(*win32gui.GetWindowRect(hwnd))
    except Exception:
        return None


def _console_hwnd() -> int | None:
    api = _windows_api()
    if api is None:
        return None
    _, _, win32console = api
    try:
        hwnd = win32console.GetConsoleWindow()
        return int(hwnd or 0) or None
    except Exception:
        return None


def center_target_and_dock_console(
    target_title: str = "Claude",
    dock_side: str = "right",
    gap: int = 16,
) -> HUDAnchorPlan:
    api = _windows_api()
    if api is None:
        return HUDAnchorPlan(target_title, None, None, note="windows api unavailable")
    win32con, win32gui, _ = api
    work = _work_area()
    target_hwnd = _find_window(target_title)
    if work is None or target_hwnd is None:
        return HUDAnchorPlan(target_title, None, None, note="target window not found or no work area")
    target_rect = _get_rect(target_hwnd)
    console_hwnd = _console_hwnd()
    console_rect = _get_rect(console_hwnd) if console_hwnd is not None else None
    plan = HUDAnchorPlan(target_title, target_rect, console_rect)
    if target_rect is None:
        plan.note = "target rect unavailable"
        return plan
    try:
        tw, th = target_rect.width, target_rect.height
        new_left = work.left + max(0, (work.width - tw) // 2)
        new_top = work.top + max(0, (work.height - th) // 2)
        win32gui.SetWindowPos(target_hwnd, 0, new_left, new_top, tw, th, win32con.SWP_NOZORDER)
        target_rect = WindowRect(new_left, new_top, new_left + tw, new_top + th)
        plan.target_rect = target_rect
        plan.centered_target = True
        if console_hwnd is not None and console_rect is not None:
            cw = min(console_rect.width or 520, max(360, work.width - tw - gap * 3))
            ch = min(console_rect.height or th, work.height - gap * 2)
            if dock_side == "left":
                cx = max(work.left + gap, target_rect.left - gap - cw)
            else:
                cx = min(work.right - cw - gap, target_rect.right + gap)
                if cx <= target_rect.right:
                    cx = max(work.left + gap, target_rect.left - gap - cw)
                    dock_side = "left"
            cy = max(work.top + gap, min(target_rect.top, work.bottom - ch - gap))
            win32gui.SetWindowPos(console_hwnd, 0, cx, cy, cw, ch, win32con.SWP_NOZORDER)
            plan.console_rect = WindowRect(cx, cy, cx + cw, cy + ch)
            plan.docked_console = True
            plan.dock_side = dock_side
        plan.applied = True
        plan.note = "target centered; console docked if available"
        return plan
    except Exception as exc:
        plan.note = f"anchor failed: {exc}"
        return plan


def maybe_apply_runtime_anchor(target_title: str = "Claude") -> dict[str, Any] | None:
    plan = center_target_and_dock_console(target_title=target_title)
    return asdict(plan)

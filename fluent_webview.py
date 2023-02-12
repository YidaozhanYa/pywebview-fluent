import os

from webview import create_window, Window
from webview import start as start_webview

import sys
import shutil
import subprocess
import logging
from enum import Enum


class BackgroundType(str, Enum):
    ACRYLIC = 'acrylic'
    FAKE_MICA_LIGHT = 'fake_mica_light'
    FAKE_MICA_DARK = 'fake_mica_dark'
    MICA_LIGHT = 'mica_light'
    MICA_DARK = 'mica_dark'


class FluentWebView:
    def __init__(
            self,
            title: str,
            background_type: BackgroundType = BackgroundType.ACRYLIC,
            debug: bool = False,
            **kwargs
    ):
        self.title = title
        self.logger = logging.getLogger('pywebview')
        self.logger.level = logging.INFO
        self.window: Window = create_window(
            title=title,
            **kwargs,
        )
        self.background_type = background_type
        self.debug = debug

    def init(self):
        match self.background_type:
            case BackgroundType.ACRYLIC:
                self.window.transparent = True
                if sys.platform == 'macos':
                    self.window.vibrancy = True
                elif sys.platform == 'linux' and (
                        shutil.which('xprop') is not None and
                        os.getenv('XDG_CURRENT_DESKTOP') == 'KDE'
                ):
                    self.logger.info('Setting blur effect for KDE')
                    effect_applied = False
                    while not effect_applied:
                        proc = subprocess.Popen(
                            ['xprop',
                             '-f', '_KDE_NET_WM_BLUR_BEHIND_REGION', '32c',
                             '-set', '_KDE_NET_WM_BLUR_BEHIND_REGION', '0',
                             '-name', self.title],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL
                        )
                        proc.wait()
                        effect_applied = proc.returncode == 0
                elif sys.platform == 'win32':
                    from ctypes import POINTER, Structure, c_bool, sizeof, windll, pointer, c_int
                    from ctypes.wintypes import DWORD, ULONG

                    class AccentPolicy(Structure):
                        _fields_ = [
                            ('AccentState', DWORD),
                            ('AccentFlags', DWORD),
                            ('GradientColor', DWORD),
                            ('AnimationId', DWORD),
                        ]

                    class WindowCompositionAttribData(Structure):
                        _fields_ = [
                            ('Attribute', DWORD),
                            ('Data', POINTER(AccentPolicy)),
                            ('SizeOfData', ULONG),
                        ]

                    webview_hwnd = self.windows_get_hwnd()

                    self.logger.info('Setting blur effect for Windows 10+')
                    set_window_composition_attribute = windll.user32.SetWindowCompositionAttribute
                    set_window_composition_attribute.restype = c_bool
                    set_window_composition_attribute.argtypes = [c_int, POINTER(WindowCompositionAttribData)]
                    accent_policy = AccentPolicy()
                    accent_policy.AccentState = 4
                    accent_policy.AccentFlags = DWORD(0x20 | 0x40 | 0x80 | 0x100)
                    accent_policy.GradientColor = DWORD(int('00FFFFFF', base=16))
                    accent_policy.AnimationId = 0
                    data = WindowCompositionAttribData()
                    data.Attribute = 19
                    data.SizeOfData = sizeof(accent_policy)
                    data.Data = pointer(accent_policy)
                    set_window_composition_attribute(webview_hwnd, pointer(data))
            case BackgroundType.FAKE_MICA_LIGHT:
                self.window.transparent = False
                self.window.evaluate_js(
                    'document.body.style.background = '
                    '"#f3f3f3 radial-gradient(#eff4f9 75%, #f3f3f3 100%) no-repeat fixed";'
                )
            case BackgroundType.FAKE_MICA_DARK:
                self.window.transparent = False
                self.window.evaluate_js(
                    'document.body.style.background = '
                    '"#202020 radial-gradient(#1a1f35 25%, #202020 100%) no-repeat fixed";'
                )
            case BackgroundType.MICA_LIGHT:
                self.window.transparent = True
                if sys.platform == 'win32':
                    from win32mica import MICAMODE, ApplyMica
                    webview_hwnd = self.windows_get_hwnd()
                    ApplyMica(webview_hwnd, MICAMODE.MICA_LIGHT)
            case BackgroundType.MICA_DARK:
                self.window.transparent = True
                if sys.platform == 'win32':
                    from win32mica import MICAMODE, ApplyMica
                    webview_hwnd = self.windows_get_hwnd()
                    ApplyMica(webview_hwnd, MICAMODE.MICA_DARK)

        self.message_box()

    def windows_get_hwnd(self) -> int:
        from ctypes import POINTER, Structure, c_bool, sizeof, windll, pointer, c_int
        from ctypes.wintypes import DWORD, ULONG
        from win32gui import EnumWindows, GetWindowText, IsWindowVisible

        webview_hwnd: int | None = None

        def enum_handler(hwnd, mouse):
            nonlocal webview_hwnd
            if IsWindowVisible(hwnd):
                if GetWindowText(hwnd) == self.title:
                    self.logger.info(f'Found window {hwnd}')
                    webview_hwnd = hwnd

        while webview_hwnd is None:
            EnumWindows(enum_handler, 0)

        return webview_hwnd

    def start(self):
        gui = None
        match sys.platform:
            case 'win32':
                gui = 'edgechromium'
            case 'linux':
                gui = 'gtk'
            case 'macos':
                gui = 'cocoa'
        start_webview(
            self.init,
            gui=gui,
            debug=self.debug
        )

    def message_box(self) -> bool:
        from time import sleep
        return_value: bool | None = None

        message_box_window = create_window(
            title=self.title,
            url='web/message_box.html',
            fullscreen=True,
            frameless=True,
            transparent=True,
            resizable=False,
        )

        while return_value is None:
            sleep(0.1)
            return_value = message_box_window.evaluate_js('return_value')

        message_box_window.destroy()
        return return_value

from webview import create_window, Window
from webview import start as start_webview
from darkdetect import isDark as is_dark

import os, sys
import shutil
import subprocess
import logging
from enum import Enum
from urllib.parse import quote


class BackgroundType(str, Enum):
    ACRYLIC = 'acrylic'
    FAKE_MICA_LIGHT = 'fake_mica_light'
    FAKE_MICA_DARK = 'fake_mica_dark'
    MICA_LIGHT = 'mica_light'
    MICA_DARK = 'mica_dark'
    AUTO_ACRYLIC = 'auto_acrylic'
    AUTO_MICA = 'auto_mica'


class FluentWebView:
    def __init__(
            self,
            title: str,
            background_type: BackgroundType = BackgroundType.ACRYLIC,
            debug: bool = False,
            startup_function: callable = None,
            **kwargs
    ):
        """
        FluentWebView class, a wrapper around pywebview
        :param title: Window title
        :param background_type: Window background type
        :param debug: Enable debug mode
        :param startup_function: Function to invoke upon starting the GUI loop
        :param kwargs: Additional arguments to be passed to create_window
        """
        self.title = title
        self.logger = logging.getLogger('pywebview')
        self.logger.level = logging.INFO
        self.window: Window = create_window(
            title=title,
            **kwargs,
        )
        new_background_type = background_type
        match background_type:
            case BackgroundType.AUTO_ACRYLIC:
                if sys.platform in ['macos', 'win32']:
                    new_background_type = BackgroundType.ACRYLIC
                elif sys.platform == 'linux' and (
                        shutil.which('xprop') is not None and
                        os.getenv('XDG_CURRENT_DESKTOP') == 'KDE'
                ):
                    new_background_type = BackgroundType.ACRYLIC
                else:
                    new_background_type = BackgroundType.FAKE_MICA_DARK if is_dark() else BackgroundType.FAKE_MICA_LIGHT
            case BackgroundType.AUTO_MICA:
                if sys.platform == 'win32' and sys.getwindowsversion().build >= 22000:
                    new_background_type = BackgroundType.MICA_DARK if is_dark() else BackgroundType.MICA_LIGHT
                else:
                    new_background_type = BackgroundType.FAKE_MICA_DARK if is_dark() else BackgroundType.FAKE_MICA_LIGHT
        self.background_type = new_background_type
        self.debug = debug
        self.startup_function = startup_function

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

        if self.startup_function is not None:
            self.startup_function(self)

    def evaluate_js(self, function_name: str, args: list | None = None, window: Window | None = None):
        """
        Evaluate JavaScript in the webview.
        :param function_name: The name of the function to call.
        :param args: The arguments to pass to the function.
        :param window: The window to evaluate the JavaScript in.
        :return: The result of the function.
        """
        string_builder: str = ''
        if args is not None:
            for arg in args:
                if isinstance(arg, str):
                    string_builder += f"decodeURIComponent('{quote(arg)}')"
                elif isinstance(arg, bool):
                    string_builder += 'true' if arg else 'false'
                else:
                    string_builder += str(arg)
                string_builder += ', '
        javascript: str = f'{function_name}({string_builder.strip(", ")});'
        if self.debug:
            print(javascript)
        if window is None:
            window = self.window
        return window.evaluate_js(javascript)

    def windows_get_hwnd(self) -> int:
        """
        Get the hWnd of the webview window on Windows.
        :return: The hWnd of the webview window.
        """
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
        """
        Start the webview.
        """
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

    def message_box(
            self,
            content: str,
            primary_button_text: str = 'OK',
            title: str = '',
            show_secondary_button: bool = False,
            secondary_button_text: str = '',
    ) -> bool:
        """
        Show a fluent message box.
        :param content: The content of the message box.
        :param primary_button_text: The text of the primary button.
        :param title: The title of the message box.
        :param show_secondary_button: Whether to show the secondary button.
        :param secondary_button_text: The text of the secondary button.
        :return: Whether the primary button was clicked.
        """
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

        self.evaluate_js(
            'showMessageBox',
            [title, content, primary_button_text, show_secondary_button, secondary_button_text],
            message_box_window
        )

        while return_value is None:
            sleep(0.1)
            try:
                return_value = message_box_window.evaluate_js('return_value')
            except KeyError:  # window closed
                return False

        message_box_window.destroy()
        return return_value

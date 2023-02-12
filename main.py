from fluent_webview import FluentWebView, BackgroundType
import darkdetect

if __name__ == '__main__':
    if darkdetect.isDark():
        background_type = BackgroundType.FAKE_MICA_DARK
    else:
        background_type = BackgroundType.FAKE_MICA_LIGHT

    FluentWebView(
        title='Fluent WebView',
        url='web/index.html',
        background_type=background_type,
        debug=True,
    ).start()

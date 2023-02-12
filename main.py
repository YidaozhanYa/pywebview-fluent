from fluent_webview import FluentWebView, BackgroundType

if __name__ == '__main__':
    def startup(self):
        self.message_box('Hello World!')


    FluentWebView(
        title='Fluent WebView',
        url='web/index.html',
        background_type=BackgroundType.AUTO_MICA,
        debug=True,
        startup_function=startup
    ).start()

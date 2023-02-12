# 🌐 PyWebView - Fluent UI (WIP)

Fluent UI for PyWebView with Acrylic and Mica support

![image-20230212184119275](https://imgsrc.baidu.com/super/pic/item/c83d70cf3bc79f3d85882ef6ffa1cd11738b298f.jpg)
![image-20230212184126021](https://imgsrc.baidu.com/super/pic/item/86d6277f9e2f0708fc6ce0c6ac24b899a801f288.jpg)

### Demo

`main.py`

```python
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
```
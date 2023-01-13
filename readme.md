Windows桌面划词程序，仅支持中译英和中译日，目前仅支持百度翻译

## 使用

鼠标双击/拖动选择文本，按快捷键(默认`Ctrl+Alt+Z`)进行翻译
![img.png](img.png)
## TODO:

- 快捷键设置完善
- 查询窗口大小根据翻译结果自适应，位置自动调整不出屏幕
- 发音
- 输入框进行翻译查询
- 添加Moji辞典
- 接入Anki
- 添加英文词典+例句
- 异常处理
- 翻译窗口添加固定不隐藏按钮

## Bugs

- 在部分软件使用（如IDEA）会因快捷键冲突而产生问题，如在IDEA可以先自行`Ctrl+C`复制需要翻译的文本，再按快捷键进行翻译。

## 参考

- [【Python】读取windows代理信息](https://www.cnblogs.com/wuruiyang/p/15928700.html)
- [python打包exe开机自动启动的实例(windows)](http://www.qb5200.com/article/373470.html)
- [如何在 pyqt 中自定义无边框窗口](https://www.cnblogs.com/zhiyiYo/p/14659981.html)

---

打包成exe命令:

```
pyinstaller -F -w -i ./asserts/翻译.ico entry.py
```
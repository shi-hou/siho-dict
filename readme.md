基于PyQt5的Windows桌面划词翻译程序, 支持百度翻译和Moji辞書, 支持将单词添加到Anki

## 使用

鼠标双击/拖动选择文本，按快捷键(默认`Ctrl+Alt+Z`)进行翻译
![img.png](img.png)

## Bugs

- 百度的发音绝大多数时候会获取失败
- 启动后第一次翻译会有卡顿现象
- 在部分软件使用（如IDEA）会因快捷键冲突而产生问题

---

打包成exe命令:

```
pyinstaller -i "assets\翻译.ico" -n "siho-dict" --add-data "assets;assets" --clean -y -w -F -D "entry.py"
```
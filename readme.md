<p align="center">
  <img width="15%" align="center" src="assets/icon/翻译.svg" alt="logo">
</p>
  <h1 align="center">
  siho-dict
</h1>
<p align="center">
  基于PyQt5的Windows桌面划词翻译/查词工具
</p>
<p align="center">
    <a style="text-decoration:none" href="https://github.com/shi-hou/siho-dict/releases">
        <img src="https://img.shields.io/github/v/release/shi-hou/siho-dict?color=%23409EFF" alt="release">
    </a>
    <a style="text-decoration:none">
        <img src="https://img.shields.io/badge/platform-windows-lightgrey" alt="platform: windows">
    </a>
    <a style="text-decoration:none">
        <img src="https://img.shields.io/github/stars/shi-hou/siho-dict?style=social" alt="stars">
    </a>
</p>

![img.png](img.png)

## 功能

- 支持划词翻译、输入翻译
- 支持有道词典、百度翻译和Moji辞書
- 支持将单词添加到Anki

## 安装

前往 [release](https://github.com/shi-hou/siho-dict/releases) 下载最新版本的zip压缩包，解压运行siho-dict.exe即可。

或者自行将代码进行打包:

```
pyinstaller -i "assets\icon\翻译.ico" -n "siho-dict" --add-data "assets;assets" --clean -y -w -F -D "entry.py"
```

## 使用

### 翻译/查词

- 鼠标双击/拖动选择文本, 按快捷键(默认`Ctrl+Alt+Z`)进行翻译/查词
- 或者在输入框中输入文本, 按下回车键进行翻译/查词

### 将单词添加到Anki

- 见Wiki，[Anki自动制卡](https://github.com/shi-hou/siho-dict/wiki/Anki%E8%87%AA%E5%8A%A8%E5%88%B6%E5%8D%A1)

## Bugs

- 百度翻译的发音绝大多数时候会获取失败
- 启动后第一次翻译会有卡顿现象

## TODO

- 添加输入框Suggest
- ...

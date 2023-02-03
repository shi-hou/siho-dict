# siho-dict
> Windows桌面划词翻译/查词工具

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/shi-hou/siho-dict?color=%23409EFF)](https://github.com/shi-hou/siho-dict/releases)

基于PyQt5的Windows桌面划词翻译/查词工具，支持有道词典、百度翻译和Moji辞書，支持将单词添加到Anki。

![img.png](img.png)

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
- 在部分软件使用（如IDEA）会因快捷键冲突而产生问题

## TODO

- 添加输入框Suggest
- ...

## Release History
- v0.2.2
  - Update: 更新Moji的Anki模板
  - Fix: 修复Moji查词面板内部可滚动问题
- v0.2.1
  - Add: 添加Anki自动同步
  - Add: 添加查无结果时提示
  - Fix: 修复有时候不显示卡片内容的问题
  - Fix: 调整有道词典样式
- v0.2.0
  - Add: 添加新的词典支持: 有道词典
  - Add: 添加缓存清理功能
  - Fix: 修复查询的单词包含“'”则不能播放音频的问题
  - Fix: 使不支持添加到Anki的单词在查词面板没有Anki按钮
- v0.1.0
  - 基础功能实现
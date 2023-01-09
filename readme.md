Windows桌面划词程序，仅支持中译英和中译日，目前仅支持百度翻译

## 使用

鼠标双击/拖动选择文本，按快捷键Ctrl+Alt+Z进行翻译

## TODO:

- ~~点击其他地方自动隐藏~~
- 结果窗口可拖动
- 发音
- 输入框进行翻译查询
- 开机自启设置
- ~~打开系统代理requests发送请求会报错问题~~
- 添加Moji辞典
- 接入Anki
- 添加英文词典+例句
- 美化
- 设置界面

## Bugs

- 有时候只按Ctrl+Alt也会触发翻译，并持续这种情况
- 在部分软件使用（如IDEA）会有因快捷键而产生的问题，在IDEA可先自行Ctrl+C复制再按快捷键Ctrl+Alt+Z进行翻译

## 参考

- [【Python】读取windows代理信息 ](https://www.cnblogs.com/wuruiyang/p/15928700.html)
- [python 程序常驻任务栏右下角显示图标](https://blog.csdn.net/m0_56708264/article/details/122263286)

---

#### 打包成exe命令:

```
pyinstaller -F -w entry.py
```
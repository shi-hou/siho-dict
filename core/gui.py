import sys
from time import sleep

import keyboard
import mouse
import pyperclip
from PyQt5.QtCore import Qt, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QLineEdit, QSystemTrayIcon, QMainWindow, QApplication
from pyqtkeybind import keybinder

from core import utils
from core.api import dict_list, baidu_trans
from core.widgets.BaseWindow import BaseWindow
from core.widgets.IGroup import IGroup
from core.widgets.ILineEdit import ILineEdit
from core.widgets.IMenu import IMenu
from core.widgets.IPage import IPage
from core.widgets.ISwitch import ISwitch
from core.widgets.ResultWidget import ResultWidget, AudioButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.trans_window = TransWindow()
        self.tray_icon = TrayIcon()
        self.setting_window = SettingWindow()

        @self.tray_icon.menu_open_setting_act.triggered.connect
        def show_setting_window():
            self.setting_window.show()
            self.setting_window.activateWindow()

        @self.setting_window.hotkey_edit.editingFinished.connect
        def slot():
            if self.setting_window.hotkey_edit.isModified():
                original_hotkey = self.setting_window.config.get('hotkey', 'Ctrl+Alt+Z')
                new_hotkey = self.setting_window.hotkey_edit.text()
                keybinder.unregister_hotkey(self.winId(), original_hotkey)
                keybinder.register_hotkey(self.winId(), new_hotkey, self.trans_window.on_hotkey)
                self.setting_window.config['hotkey'] = new_hotkey
                utils.update_config(self.setting_window.config)

        @self.tray_icon.menu_open_trans_act.triggered.connect
        def menu_open_trans_act_triggered():
            self.trans_window.content_widget.hide()
            self.trans_window.show()

        @self.tray_icon.activated.connect
        def tray_icon_activated(reason):
            if reason == QSystemTrayIcon.Trigger:
                self.trans_window.content_widget.hide()
                self.trans_window.show()

        self.tray_icon.show()


class TransWindow(BaseWindow):
    trans_signal = pyqtSignal(str, dict, int, int)

    def __init__(self):
        self.input_edit = QLineEdit()
        super().__init__(title_bar_slot=self.input_edit)
        self.fix_btn = self.addTitleBarButton(icon=utils.get_resources_path('固定_line.svg'))
        self.result_widget = ResultWidget(audio_btn_color=AudioButton.BLUE)
        self.audio_btn_color = None
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(1)
        self.trans_loader = None
        self.fix_not_hidden = False
        self.init()

    def init(self):
        self.trans_signal.connect(self.show_trans)

        self.setFixedWidth(309)
        self.setFixedHeight(500)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.Tool)
        self.content_widget.hide()

        self.close_btn.clicked.connect(self.hide)

        utils.addMouseEvent(self, self.mouse_on_click, mouse_btn=mouse.LEFT, btn_type=mouse.DOWN)

        @self.input_edit.returnPressed.connect
        def input_return_pressed():
            if self.input_edit.isModified():
                input_txt = self.input_edit.text().strip()
                if input_txt == '':
                    return
                self.trans_loader = TransLoader(self.trans_signal, self.frameGeometry(), input_txt)
                self.thread_pool.start(self.trans_loader)

        fold_btn = self.addTitleBarButton(icon=utils.get_resources_path('折叠面板.svg'))

        @fold_btn.clicked.connect
        def fold_button_on_click():
            self.content_widget.setHidden(not self.content_widget.isHidden())

        @self.fix_btn.clicked.connect
        def fix_button_on_click():
            self.setFixNotHidden(not self.fix_not_hidden)

        self.input_edit.setProperty('class', 'trans-input-edit')
        page = IPage()
        page.addWidget(self.result_widget)
        self.setPage(page)

    def hide(self) -> None:
        self.setFixNotHidden(False)
        self.input_edit.clear()
        self.content_widget.hide()
        BaseWindow.hide(self)

    @pyqtSlot(str, dict, int, int)
    def show_trans(self, input_text, result_dict, x, y):
        print('Ohhhh')
        self.input_edit.setText(input_text)
        self.input_edit.clearFocus()
        self.content_widget.setHidden(input_text == '')
        self.result_widget.setResult(result_dict)
        if not self.fix_not_hidden:
            self.move(x, y)
        self.show()

    def on_hotkey(self):
        x, y = mouse.get_position()
        self.trans_loader = TransLoader(self.trans_signal, QRect(x, y, self.width(), self.height()))
        self.thread_pool.start(self.trans_loader)

    def mouse_on_click(self):
        if self.fix_not_hidden:
            return
        x, y = mouse.get_position()
        if not self.isHidden() and (
                QPoint(x, y) not in self.geometry()
                or (
                        self.content_widget.isHidden()
                        and QPoint(x - self.x(), y - self.y()) not in self.title_bar.geometry())):
            self.hide()

    def setFixNotHidden(self, value: bool):
        self.fix_not_hidden = value
        self.fix_btn.setIcon(QIcon(QPixmap(utils.get_resources_path('固定_fill.svg' if value else '固定_line.svg'))))


class TransLoader(QRunnable):

    def __init__(self, trans_signal, geometry: QRect, input_txt=None):
        super().__init__()
        self.trans_signal = trans_signal
        self.geometry = geometry
        self.input_txt = input_txt

    def run(self):
        if self.input_txt is not None:  # 来自输入框
            current_txt = self.input_txt
        else:  # 来自划词
            former_copy = pyperclip.paste()  # 用于还原剪切板
            keyboard.press_and_release('ctrl+c')
            sleep(0.1)
            current_txt = pyperclip.paste()
            pyperclip.copy(former_copy)  # 还原剪切版
        current_txt = current_txt.strip().replace('\n', ' ')
        if current_txt == '':  # 只显示title_bar, 不翻译
            self.geometry.setHeight(BaseWindow.title_bar_height)
            result_dict = {}
        else:
            result_dict = baidu_trans(current_txt)

        desktop_geometry = QApplication.desktop().availableGeometry()

        # 0 <= show_x <= desktop_width - window_width
        show_x = max(0, min(self.geometry.x(), desktop_geometry.width() - self.geometry.width()))
        # 0 <= show_y <= desktop_height - window_height
        show_y = max(0, min(self.geometry.y(), desktop_geometry.height() - self.geometry.height()))

        self.trans_signal.emit(current_txt, result_dict, show_x, show_y)


class SettingWindow(BaseWindow):
    def __init__(self):
        super().__init__(title='设置')
        self.config = utils.get_config()
        self.hotkey_edit = ILineEdit()
        self.init()

    def init(self):
        self.setFixedSize(800, 500)

        setting_page = IPage()
        self.setPage(setting_page)

        basic_setting_group = IGroup('基础设置')
        auto_run_switch = ISwitch(on=utils.get_auto_run())

        @auto_run_switch.toggled.connect
        def slot():
            utils.set_auto_run(auto_run_switch.isToggled())

        basic_setting_group.addRow('开机自启', auto_run_switch)

        self.hotkey_edit.setText(self.config.get('hotkey', 'Ctrl+Alt+Z'))
        basic_setting_group.addRow('热键', self.hotkey_edit)

        setting_page.addWidget(basic_setting_group)

        dict_setting_group = IGroup('词典设置', '目前仅支持百度翻译，因此暂时无法设置词典，后续将支持Moji辞書、必应词典等（咕咕咕）')
        dict_settings = self.config.get('dict', {dict_list[0]['name']: {'on': True}})
        for d in dict_list:
            name = d.get('name')
            enable = d.get('enable', False)
            switch = ISwitch(on=enable and dict_settings.get(name, {}).get("on", False))
            switch.setProperty('name', name)
            switch.setEnabled(False)  # TODO 等字典多了再开放更改

            @switch.toggled.connect
            def slot():
                toggled_switch = self.sender()
                dict_name = toggled_switch.property('name')
                one_dict_setting = dict_settings.get(dict_name, {})
                one_dict_setting['on'] = toggled_switch.isToggled()
                dict_settings[dict_name] = one_dict_setting
                self.config['dict'] = dict_settings
                utils.update_config(self.config)

            dict_setting_group.addRow(d.get('title'), switch, utils.get_resources_path(d.get('icon')))

        setting_page.addWidget(dict_setting_group)

        test_setting_group = IGroup('test')
        test_setting_group.addRow('test1', ISwitch())
        test_setting_group.addRow('test2', ISwitch())
        test_setting_group.addRow('test3', ISwitch())
        setting_page.addWidget(test_setting_group)

        setting_page.addSpacing(100)


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon(QPixmap(utils.get_resources_path('翻译.svg'))))
        self.setToolTip('划词翻译')
        self.menu = IMenu()
        self.menu_open_trans_act = self.menu.addAction('显示翻译窗口')
        self.menu_open_setting_act = self.menu.addAction('设置', utils.get_resources_path('设置.svg'))
        self.menu_quit_act = self.menu.addAction('退出', utils.get_resources_path('退出.svg'))
        self.setContextMenu(self.menu)

        @self.menu_quit_act.triggered.connect
        def exit_app():
            self.hide()
            QApplication.exit()

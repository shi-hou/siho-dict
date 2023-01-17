from time import sleep

import keyboard
import mouse
import pyperclip
from PyQt5.QtCore import Qt, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QPoint, QRect, QThread
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QLineEdit, QSystemTrayIcon, QMainWindow, QApplication, QVBoxLayout
from pyqtkeybind import keybinder

from core import utils
from core.dicts import dicts, Dict
from core.widgets import BaseWindow, IPage, ILineEdit, IGroup, ISwitch, IMenu, ResultListWidget


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
                original_hotkey = utils.get_config().get('hotkey', 'Ctrl+Alt+Z')
                new_hotkey = self.setting_window.hotkey_edit.text()
                keybinder.unregister_hotkey(self.winId(), original_hotkey)
                keybinder.register_hotkey(self.winId(), new_hotkey, self.trans_window.on_hotkey)
                utils.update_config({'hotkey': new_hotkey})

        @self.tray_icon.menu_open_trans_act.triggered.connect
        def menu_open_trans_act_triggered():
            self.trans_window.content_widget.hide()
            self.trans_window.show()

        @self.tray_icon.activated.connect
        def tray_icon_activated(reason):
            if reason == QSystemTrayIcon.Trigger:
                self.trans_window.content_widget.hide()
                self.trans_window.show()

        for switch in self.setting_window.dict_switch_list:
            switch.toggled.connect(self.dict_on_switch_toggled)

        self.tray_icon.show()

    def dict_on_switch_toggled(self):
        toggled_switch = self.setting_window.sender()
        index = toggled_switch.property('index')
        on = toggled_switch.isToggled()
        dicts.setOn(index, on)
        self.trans_window.result_list_widget.reset()


class TransWindow(BaseWindow):
    show_signal = pyqtSignal(str, int, int)
    trans_signal = pyqtSignal(int, dict)

    def __init__(self):
        self.input_edit = QLineEdit()
        super().__init__(title_bar_slot=self.input_edit)
        self.fix_btn = self.addTitleBarButton(icon=utils.get_resources_path('固定_line.svg'))
        self.result_list_widget = ResultListWidget()
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(4)
        self.window_show_worker = None
        self.trans_loaders = []
        self.fix_not_hidden = False
        self.init()

    def init(self):
        self.trans_signal.connect(self.show_trans_result)
        self.show_signal.connect(self.show_window)

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
                self.result_list_widget.clear()
                input_txt = self.input_edit.text().strip()
                if input_txt == '':
                    return
                self.show_window = self.WindowShowWorker(self.show_signal, self.frameGeometry(), input_txt)
                self.thread_pool.start(self.show_window)

        fold_btn = self.addTitleBarButton(icon=utils.get_resources_path('折叠面板.svg'))

        @fold_btn.clicked.connect
        def fold_button_on_click():
            self.content_widget.setHidden(not self.content_widget.isHidden())

        @self.fix_btn.clicked.connect
        def fix_button_on_click():
            self.setFixNotHidden(not self.fix_not_hidden)

        self.input_edit.setProperty('class', 'trans-input-edit')
        page = IPage()
        layout = QVBoxLayout()
        layout.addWidget(self.result_list_widget)
        page.addLayout(layout)
        self.setPage(page)

    def hide(self) -> None:
        self.setFixNotHidden(False)
        self.input_edit.clear()
        self.content_widget.hide()
        BaseWindow.hide(self)

    @pyqtSlot(str, int, int)
    def show_window(self, input_text, x, y):
        self.input_edit.setText(input_text)
        self.input_edit.clearFocus()
        has_content = input_text != ''
        self.content_widget.setHidden(not has_content)
        if not self.fix_not_hidden:
            self.move(x, y)
        self.show()
        if has_content:
            self.result_list_widget.loading()
            self.trans_loaders = []
            for i in range(len(dicts.on_dict)):
                trans_loader = self.TransLoader(i, self.trans_signal, input_text)
                self.trans_loaders.append(trans_loader)
                self.thread_pool.start(trans_loader)

    @pyqtSlot(int, dict)
    def show_trans_result(self, index, result_dict):
        self.result_list_widget.widget_list[index].setResult(result_dict)

    def on_hotkey(self):
        for loader in self.trans_loaders:
            loader.stop()
        self.result_list_widget.clear()
        x, y = mouse.get_position()
        self.window_show_worker = self.WindowShowWorker(self.show_signal, QRect(x, y, self.width(), self.height()))
        self.thread_pool.start(self.window_show_worker)

    def mouse_on_click(self):
        """点击窗口外，隐藏窗口"""
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

    class WindowShowWorker(QRunnable):
        def __init__(self, show_signal, geometry: QRect, input_txt=None):
            super().__init__()
            self.show_signal = show_signal
            self.geometry = geometry
            self.input_txt = input_txt

        def run(self) -> None:
            if self.input_txt is not None:  # 来自输入框
                current_txt = self.input_txt
            else:  # 来自划词
                former_copy = pyperclip.paste()  # 用于还原剪切板
                keyboard.press_and_release('ctrl+c')
                sleep(0.1)
                current_txt = pyperclip.paste()
                pyperclip.copy(former_copy)  # 还原剪切版
            current_txt = current_txt.strip().replace('\n', ' ')
            if current_txt == '':  # 只显示title_bar
                self.geometry.setHeight(BaseWindow.title_bar_height)

            # 使窗口不超出主屏幕
            # 0 <= show_x <= desktop_width - window_width
            # 0 <= show_y <= desktop_height - window_height
            desktop_geometry = QApplication.desktop().availableGeometry()
            show_x = max(0, min(self.geometry.x(), desktop_geometry.width() - self.geometry.width()))
            show_y = max(0, min(self.geometry.y(), desktop_geometry.height() - self.geometry.height()))

            self.show_signal.emit(current_txt, show_x, show_y)

    class TransLoader(QRunnable):

        def __init__(self, index, trans_signal, text: str):
            super().__init__()
            self.index = index
            self.trans_signal = trans_signal
            self.text = text
            self.is_running = True

        def run(self):
            retries = 3
            from_lang = utils.check_language(self.text)
            for i in range(retries):
                if not self.is_running:
                    return
                try:
                    result = dicts.on_dict[self.index].do_trans(self.text, from_lang)
                    self.trans_signal.emit(self.index, result)
                    return
                except Exception as err:
                    print(err)
                    pass
            self.trans_signal.emit(self.index, Dict.message_result('翻译出现异常'))

        def stop(self):
            self.is_running = False


class SettingWindow(BaseWindow):
    def __init__(self):
        super().__init__(title='设置')
        self.hotkey_edit = ILineEdit()
        self.dict_switch_list = []
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

        self.hotkey_edit.setText(utils.get_config().get('hotkey', 'Ctrl+Alt+Z'))
        basic_setting_group.addRow('热键', self.hotkey_edit)

        setting_page.addWidget(basic_setting_group)

        dict_setting_group = IGroup('词典设置')
        for i, d in enumerate(dicts.all_dict):
            switch = ISwitch(on=d.on)
            switch.setProperty('index', i)
            switch.setEnabled(d.able)
            self.dict_switch_list.append(switch)

            dict_setting_group.addRow(d.title, switch, utils.get_resources_path(d.icon))

        setting_page.addWidget(dict_setting_group)

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

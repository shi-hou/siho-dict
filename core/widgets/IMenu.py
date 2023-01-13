from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu, QAction, QWidgetAction, QWidget, QHBoxLayout, QLabel


class IMenu(QMenu):
    def __init__(self):
        super().__init__()
        self.items = []
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.5)

    def addAction(self, text: str = '', icon_path: str = None) -> QAction:
        height = 35
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        text_label = QLabel(text)
        text_label.setProperty('class', 'i-menu-item-text')
        layout.addWidget(text_label)
        layout.addStretch(1)
        if icon_path is not None:
            icon_label = QLabel()
            icon_label.setFixedWidth(20)
            icon_label.setFixedHeight(20)
            icon_path = icon_path.replace('\\', '/')  # url()用“\”会不生效
            icon_label.setStyleSheet(f'border-image: url({icon_path});')
            layout.addWidget(icon_label)
        layout.addSpacing(20)
        widget = QWidget()
        widget.setFixedHeight(height)
        widget.setLayout(layout)
        index = len(self.items)
        if index > 0:
            self.addSeparator()
            widget.setProperty('class', 'i-menu-item-last')
            if index - 1 > 0:
                self.items[index - 1].setProperty('class', 'i-menu-item')
        else:
            widget.setProperty('class', 'i-menu-item-first')
        self.items.append(widget)
        action = QWidgetAction(self)
        action.setDefaultWidget(widget)
        QMenu.addAction(self, action)
        return action

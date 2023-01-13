from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel


class IRow(QWidget):
    def __init__(self, labelText: str = '', widget: QWidget = None, icon: str = None):
        super().__init__()
        self.setFixedHeight(50)
        self.setAttribute(Qt.WA_StyledBackground)
        self.row_layout = QHBoxLayout()
        self.setLayout(self.row_layout)
        self.row_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_with_border_bottom = QWidget()

        if icon is not None:
            icon_label = QLabel()
            icon_label.setFixedHeight(30)
            icon_label.setFixedWidth(30)
            icon = icon.replace('\\', '/')  # url()用“\”会不生效
            icon_label.setStyleSheet(f'border-image: url({icon}); border-radius: 10px;')
            self.row_layout.addWidget(icon_label)

        layout_with_border_bottom = QHBoxLayout()
        layout_with_border_bottom.setContentsMargins(0, 0, 20, 0)
        self.widget_with_border_bottom.setLayout(layout_with_border_bottom)
        text_label = QLabel(labelText)
        text_label.setProperty('class', 'i-row-text-label')
        layout_with_border_bottom.addWidget(text_label)
        layout_with_border_bottom.addStretch(1)
        layout_with_border_bottom.addWidget(widget, alignment=Qt.AlignVCenter)
        self.row_layout.addWidget(self.widget_with_border_bottom)
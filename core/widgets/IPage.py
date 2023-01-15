from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLayout, QScrollArea


class IPage(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground)
        page_widget = QWidget()
        self.page_layout = QVBoxLayout()
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.page_layout)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        page_widget.setLayout(self.page_layout)
        self.setWidget(page_widget)

    def addWidget(self, widget: QWidget):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        layout.addWidget(widget)
        layout.addStretch(1)
        self.page_layout.addLayout(layout)

    def addLayout(self, layout: QLayout):
        self.page_layout.addLayout(layout)

    def addStretch(self, stretch):
        self.page_layout.addStretch(stretch)

    def addSpacing(self, spacing):
        self.page_layout.addSpacing(spacing)

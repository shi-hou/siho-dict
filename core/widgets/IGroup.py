from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout


class IGroup(QWidget):
    def __init__(self, title=None, explain=None):
        super().__init__()
        self.rows = []
        self.form_layout = QVBoxLayout()
        self.title_label = QLabel()
        self.init(title, explain)

    def init(self, title, explain):
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedWidth(500)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 40, 0, 0)
        layout.addWidget(self.title_label)
        self.setLayout(layout)
        self.setTitle(title)
        self.title_label.setProperty('class', 'i-group-title')

        form_widget = QWidget()
        self.form_layout.setContentsMargins(20, 0, 0, 0)
        self.form_layout.setSpacing(0)
        form_widget.setLayout(self.form_layout)
        form_widget.setProperty('class', 'i-group-form')
        layout.addWidget(form_widget)

        if explain is not None:
            explain_label = QLabel(explain)
            explain_label.setWordWrap(True)
            explain_label.setProperty('class', 'i-group-explain')
            layout.addWidget(explain_label)

    def setTitle(self, title=None):
        if title is not None:
            self.title_label.setText(title)
            self.title_label.show()
        else:
            self.title_label.hide()

    def addRow(self, labelText: str = '', widget: QWidget = None, icon: str = None):
        row = self.IRow(labelText, widget, icon)
        row_index = len(self.rows)
        if row_index > 0:
            self.rows[row_index - 1].widget_with_border_bottom.setProperty('class', 'i-row-with-bottom-border')
        self.form_layout.addWidget(row)
        self.rows.append(row)

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

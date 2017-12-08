import sys
import os
import qtawesome as qta
import functools

from PyQt5.QtWidgets import (QApplication,
                             QMainWindow,
                             QWidget,
                             QVBoxLayout,
                             QHBoxLayout,
                             QTabWidget,
                             QGroupBox,
                             QLineEdit,
                             QFormLayout,
                             QScrollArea,
                             QPushButton,
                             QLabel,
                             QCheckBox)
from PyQt5.QtGui import QIcon, QDesktopServices, QPalette
from PyQt5.QtCore import Qt, QUrl
from i18n import t

from happypanda.common import constants, utils, config

app = None

class SettingsTabs(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_ui()

    def create_ui(self):
        cfg = config.ConfigNode.get_all()
        for ns in sorted(config.ConfigNode.default_namespaces):
            w = QWidget()
            wlayout = QFormLayout(w)
            for k, n in sorted(cfg[ns].items()):
                help_w = QPushButton(qta.icon("fa.question-circle"), "")
                help_w.setFlat(True)
                help_w.setToolTip(n.description)
                help_w.setToolTipDuration(9999999999)
                q = QWidget()
                q_l = QHBoxLayout(q)
                q_l.addWidget(help_w)
                q_l.addWidget(QLabel(k))
                wlayout.addRow(q, self.get_setting_input(k, n))
            sarea = QScrollArea(self)
            sarea.setWidget(w)
            sarea.setWidgetResizable(True)
            sarea.setBackgroundRole(QPalette.Light)
            self.addTab(sarea, ns)

    def get_setting_input(self, ns, node):
        input_w = None
        if node.type_ == dict:
            input_w = QWidget()
            input_l = QFormLayout(input_w)
            for k, v in sorted(node.default.items()):
                real_v = node.value.get(k, v)
                if type(v) == bool:
                    i = QCheckBox()
                    i.setChecked(real_v)
                    i.stateChanged.connect(
                        functools.partial(lambda w, key, value, s: self.set_dict_value(key, s, node, type(value), w),
                                          i, k, v))
                else:
                    i = QLineEdit()
                    i.setText(str(real_v))
                    i.textChanged.connect(
                        functools.partial(lambda w, key, value, s: self.set_dict_value(key, s, node, type(value), w),
                                          i, k, v))
                input_l.addRow(k, i)
        elif node.type_ == bool:
            input_w = QCheckBox()
            input_w.setChecked(node.value)
            input_w.stateChanged.connect(lambda s: self.set_value(node, s, input_w))
        else:
            input_w = QLineEdit()
            input_w.setText(str(node.value))
            input_w.textChanged.connect(lambda s: self.set_value(node, s, input_w))
        q = QWidget()
        q_l = QHBoxLayout(q)
        q_l.addWidget(input_w)
        return q

    def set_dict_value(self, k, v, node, type_, widget):
        try:
            v = type_(v)
            d = node.value.copy()
            d.update({k:v})
            node.value = d
            widget.setStyleSheet("background: rgba(137, 244, 66, 0.2);")
        except:
            widget.setStyleSheet("background: rgba(244, 92, 65, 0.2);")
        config.config.save()

    def set_value(self, node, value, widget):
        try:
            v = node.type_(value)
            node.value = v
            config.config.save()
            widget.setStyleSheet("background: rgba(137, 244, 66, 0.2);")
        except:
            widget.setStyleSheet("background: rgba(244, 92, 65, 0.2);")


class Window(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server_started = False
        self.client_started = False
        self.start_ico = qta.icon("fa.play", color="#41f46b")
        self.stop_ico = qta.icon("fa.stop", color="#f45f42")

        self.create_ui()

    def create_ui(self):
        w = QWidget(self)
        settings_group = QGroupBox(t("", default="Configuration"), w)
        settings_group_l = QVBoxLayout(settings_group)
        settings = SettingsTabs()
        settings_group_l.addWidget(settings)

        buttons = QGroupBox(w)
        self.server_btn = QPushButton(self.start_ico, t("", default="Start server"))
        self.server_btn.clicked.connect(self.toggle_server)
        self.server_btn.setShortcut(Qt.CTRL|Qt.Key_S)

        self.webclient_btn = QPushButton(self.start_ico, t("", default="Start webclient"))
        self.webclient_btn.clicked.connect(self.toggle_client)
        self.webclient_btn.setShortcut(Qt.CTRL|Qt.Key_W)

        open_config_btn = QPushButton(qta.icon("fa.cogs"), t("", default="Open configuration"))
        open_config_btn.clicked.connect(self.open_cfg)
        open_config_btn.setShortcut(Qt.CTRL|Qt.Key_C)

        for b in (self.server_btn, self.webclient_btn, open_config_btn):
            b.setFixedHeight(40)
        button_layout = QHBoxLayout(buttons)
        button_layout.addWidget(self.server_btn)
        button_layout.addWidget(self.webclient_btn)
        button_layout.addWidget(open_config_btn)

        main_layout = QVBoxLayout(w)
        main_layout.addWidget(settings_group)
        main_layout.addWidget(buttons)
        self.setCentralWidget(w)

    def open_cfg(self):
        QDesktopServices.openUrl(QUrl(constants.config_path, QUrl.TolerantMode))

    def toggle_server(self):
        self.server_started = not self.server_started
        if self.server_started:
            self.server_btn.setText(t("", default="Stop server"))
            self.server_btn.setIcon(self.stop_ico)
        else:
            self.server_btn.setText(t("", default="Start server"))
            self.server_btn.setIcon(self.start_ico)

    def toggle_client(self):
        self.client_started = not self.client_started
        if self.client_started:
            self.webclient_btn.setText(t("", default="Stop webclient"))
            self.webclient_btn.setIcon(self.stop_ico)
        else:
            self.webclient_btn.setText(t("", default="Start webclient"))
            self.webclient_btn.setIcon(self.start_ico)

if __name__ == "__main__":
    utils.setup_i18n()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(constants.dir_static, "favicon.ico")))
    app.setApplicationDisplayName("HappyPanda X")
    app.setApplicationName("HappyPanda X")
    app.setApplicationVersion(".".join(str(x) for x in constants.version))
    app.setOrganizationDomain("Twiddly")
    app.setOrganizationName("Twiddly")
    app.setDesktopFileName("HappyPanda X")

    window = Window()
    window.resize(600, 600)
    window.show()

    sys.exit(app.exec())

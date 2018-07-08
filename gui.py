import happypanda.common.patch
import sys
if __name__ == '__mp_main__' or (__name__ == '__main__' and len(
        sys.argv) >= 2 and sys.argv[1] == '--multiprocessing-fork'):
    happypanda.common.patch.patch()

import multiprocessing as mp  # noqa: E402
from happypanda import main  # noqa: E402

import os  # noqa: E402
import functools  # noqa: E402
import signal  # noqa: E402
import webbrowser  # noqa: E402
import pathlib  # noqa: E402

from multiprocessing import Process, queues  # noqa: E402
from happypanda.common import constants  # noqa: E402

if __name__ == '__main__':
    mp.set_start_method("spawn")

# This is required to be here or else multiprocessing won't work when running in a frozen state!
# I had a hell of a time debugging this :(


class RedirectProcess(Process):

    def __init__(self, streamqueue, exitqueue=None, initializer=None, **kwargs):
        super().__init__(**kwargs)
        assert initializer is None or callable(initializer)
        self.streamqueue = streamqueue
        self.exitqueue = exitqueue
        self.initializer = initializer

    def run(self):
        sys.stdout = self.streamqueue
        sys.stderr = self.streamqueue

        if self.initializer:
            self.initializer()
        if self._target:  # HACK: don't access private variables!
            e = self._target(*self._args, **self._kwargs)
            if self.exitqueue is not None:
                self.exitqueue.put(e)


class StreamQueue(queues.Queue):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, ctx=mp.get_context())

    def write(self, msg):
        if not isinstance(msg, str):
            msg = str(msg)
        self.put(msg)

    def flush(self):
        pass


def from_gui():
    constants.from_gui = True


if __name__ == "__main__":
    mp.freeze_support()

import psutil  # noqa: E402
import qtawesome as qta  # noqa: E402

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
                             QMessageBox,
                             QDialog,
                             QSystemTrayIcon,
                             QMenu,
                             QFileDialog,
                             QPlainTextEdit,
                             QCheckBox,
                             QSpinBox)  # noqa: E402
from PyQt5.QtGui import QIcon, QPalette, QMouseEvent  # noqa: E402
from PyQt5.QtCore import Qt, QDir, pyqtSignal, QEvent  # noqa: E402
from i18n import t  # noqa: E402
from threading import Thread, Timer  # noqa: E402

from happypanda.common import utils, config  # noqa: E402
from happypanda.core.commands import io_cmd  # noqa: E402
from happypanda.core import db  # noqa: E402
import HPtoHPX  # noqa: E402

if constants.is_posix:
    # need to make a request or else it won't work in other processes
    # related to https://github.com/requests/requests/issues/3752
    import requests  # noqa: E402
    try:
        requests.get("https://google.com", timeout=0.1)
    except (requests.ConnectionError, requests.Timeout):
        pass

app = None
exitcode = None

SQueue = None
SQueueExit = None


def kill_proc_tree(pid, sig=signal.SIGTERM, include_parent=True,
                   timeout=None, on_terminate=None):
    """Kill a process tree (including grandchildren) with signal
    "sig" and return a (gone, still_alive) tuple.
    "on_terminate", if specified, is a callabck function which is
    called as soon as a child terminates.
    """
    if pid == os.getpid():
        raise RuntimeError("I refuse to kill myself")
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        p.send_signal(sig)
    gone, alive = psutil.wait_procs(children, timeout=timeout,
                                    callback=on_terminate)
    return (gone, alive)


class TextViewer(QPlainTextEdit):
    """
    A read-only embedded console
    """

    write = pyqtSignal(str)

    def __init__(self, streamqueue, parent=None):
        super().__init__(parent)
        self.stream = streamqueue
        self.setMaximumBlockCount(999)
        self.setReadOnly(True)
        self.write.connect(self.w)
        if self.stream:
            t = Thread(target=self.poll_stream)
            t.daemon = True
            t.start()

    def w(self, s):
        s = s.strip()
        if s:
            self.appendPlainText('>: ' + s if s != '\n' else s)

    def poll_stream(self):
        while True:
            self.write.emit(self.stream.get())


class PathLineEdit(QLineEdit):
    """
    A lineedit which open a filedialog on right/left click
    Set dir to false if you want files.
    """

    def __init__(self, parent=None, dir=True, filters=""):
        super().__init__(parent)
        self.folder = dir
        self.filters = filters
        self.setPlaceholderText('Left-click to open folder explorer')
        self.setToolTip('Left-click to open folder explorer')

    def openExplorer(self):
        if self.folder:
            path = QFileDialog.getExistingDirectory(self,
                                                    'Choose folder', QDir.homePath())
        else:
            path = QFileDialog.getOpenFileName(self,
                                               'Choose file', QDir.homePath(), filter=self.filters)
            path = path[0]
        if len(path) != 0:
            self.setText(path)

    def mousePressEvent(self, event):
        assert isinstance(event, QMouseEvent)
        if len(self.text()) == 0:
            if event.button() == Qt.LeftButton:
                self.openExplorer()
        super().mousePressEvent(event)


class ConvertHP(QDialog):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
        self._source = ""
        self._destination = ""
        self._rar = ""
        self._process = 0
        self._archive = False
        self._delete = False
        self._dev = False
        self._limit = -1
        self._offset = 0
        self._args_edit = QLineEdit(self)
        self.args = []
        self.create_ui()
        self.setMinimumWidth(500)

    def create_ui(self):
        lf = QFormLayout(self)

        source_edit = PathLineEdit(self, False, "happypanda.db")
        source_edit.textChanged.connect(self.on_source)
        lf.addRow(t("gui.t-old-hp-file", default="Old HP database file") + ':', source_edit)

        rar_edit = PathLineEdit(self, False)
        rar_edit.setPlaceholderText(t("gui.t-optional", default="Optional"))
        rar_edit.textChanged.connect(self.on_rar)
        lf.addRow(t("gui.t-rar-path", default="RAR tool path") + ':', rar_edit)
        rar_edit.setText(config.unrar_tool_path.value)

        limit_box = QSpinBox(self)
        limit_box.valueChanged.connect(self.on_limit)
        lf.addRow(t("gui.t-limit", default="Limit") + ':', limit_box)
        limit_box.setRange(-1, 2147483647)

        offset_box = QSpinBox(self)
        offset_box.valueChanged.connect(self.on_offset)
        lf.addRow(t("gui.t-offset", default="Offset") + ':', offset_box)
        offset_box.setRange(0, 2147483647)

        archive_box = QCheckBox(self)
        archive_box.stateChanged.connect(self.on_archive)
        lf.addRow(t("gui.t-skip-archive", default="Skip archives") + ':', archive_box)

        delete_db = QCheckBox(self)
        delete_db.setChecked(self._delete)
        delete_db.stateChanged.connect(self.on_delete)
        lf.addRow(t("gui.t-delete-target", default="Delete target database if it already exists") + ':', delete_db)

        dev_box = QCheckBox(self)
        dev_box.stateChanged.connect(self.on_dev)
        dev_box.setChecked(constants.dev_db)
        lf.addRow(t("gui.t-dev-mode", default="Dev Mode") + ':', dev_box)

        lf.addRow(t("gui.t-command", default="Command") + ':', self._args_edit)
        convert_btn = QPushButton(t("gui.b-convert", default="Convert"))
        convert_btn.clicked.connect(self.convert)
        lf.addRow(convert_btn)

    def on_source(self, v):
        self._source = v
        self.update_label()

    def on_rar(self, v):
        self._rar = v
        self.update_label()

    def on_process(self, v):
        self._process = v
        self.update_label()

    def on_archive(self, v):
        self._archive = v
        self.update_label()

    def on_limit(self, v):
        self._limit = v
        self.update_label()

    def on_offset(self, v):
        self._offset = v
        self.update_label()

    def on_delete(self, v):
        self._delete = v
        self.update_label()

    def on_dev(self, v):
        self._dev = v
        self.update_label()

    def update_label(self):
        self.args = []
        self.args .append(os.path.normpath(self._source))
        if config.dialect.value == constants.Dialect.SQLITE:
            self.args .append(constants.db_path_dev if self._dev else constants.db_path)
        else:
            self.args .append(str(db.make_db_url(constants.db_name_dev if self._dev else constants.db_name)))
        if self._rar:
            self.args .append("--rar")
            self.args .append(os.path.normpath(self._rar))
        if self._archive:
            self.args .append("--skip-archive")
        if self._delete:
            self.args .append("--delete-target")
        self.args .append("--limit")
        self.args .append(str(self._limit))
        self.args .append("--offset")
        self.args .append(str(self._offset))

        self._args_edit.setText(" ".join(self.args))
        self.adjustSize()

    def convert(self):
        if self.args:
            self._parent.activate_output.emit()
            p = RedirectProcess(SQueue, target=HPtoHPX.main, args=(self.args,))
            p.start()
            self._parent.processes.append(p)
            Thread(target=self._parent.watch_process, args=(None, p)).start()
            self.close()


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
                if not n.hidden:
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
                if real_v is None:
                    real_v = "null"
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
            if isinstance(node.value, bool):
                str_value = "true" if node.value else "false"
            elif node.value is None:
                str_value = "null"
            else:
                str_value = str(node.value)
            input_w.setText(str_value)
            input_w.textChanged.connect(lambda s: self.set_value(node, s, input_w))
        q = QWidget()
        q_l = QHBoxLayout(q)
        q_l.addWidget(input_w)
        return q

    def value_type(self, v, type_):
        if not isinstance(type_, tuple):
            type_ = (type_,)
        if v == "null":
            v = None
        elif v in ("false", "true") and bool in type_:
            v = True if v == "true" else False
        else:
            for i in type_:
                try:
                    v = i(v)
                    break
                except BaseException:
                    pass
        return v

    def set_dict_value(self, k, v, node, type_, widget):
        try:
            v = self.value_type(v, type_)
            d = node.value.copy()
            d.update({k: v})
            node.value = d
            widget.setStyleSheet("background: rgba(137, 244, 66, 0.2);")
        except BaseException:
            widget.setStyleSheet("background: rgba(244, 92, 65, 0.2);")
        config.config.save()

    def set_value(self, node, value, widget):
        try:
            v = self.value_type(value, node.type_)
            node.value = v
            config.config.save()
            widget.setStyleSheet("background: rgba(137, 244, 66, 0.2);")
        except BaseException:
            widget.setStyleSheet("background: rgba(244, 92, 65, 0.2);")


class Window(QMainWindow):

    activate_output = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processes = []
        self.tray = QSystemTrayIcon(self)
        self.tray.show()
        self.closing = False
        self.forcing = False
        self.server_started = False
        self.client_started = False
        self.output_tab_idx = 0
        self.force_kill = False
        self.start_ico = QIcon(constants.favicon_path
                               )  # qta.icon("fa.play", color="#41f46b")
        self.stop_ico = qta.icon("fa.stop", color="#f45f42")
        self.server_process = None
        self.webclient_process = None
        self.create_ui()

        self.activate_output.connect(lambda: self.main_tab.setCurrentIndex(self.output_tab_idx))

        if config.gui_autostart_server.value:
            self.toggle_server()

    def create_ui(self):
        w = QWidget(self)
        self.main_tab = QTabWidget(self)
        self.viewer = TextViewer(SQueue, self.main_tab)
        settings_widget = QWidget(self.main_tab)
        self.output_tab_idx = self.main_tab.addTab(self.viewer, t("gui.mi-output", default="Output"))
        self.main_tab.addTab(settings_widget, t("gui.mi-config", default="Configuration"))

        settings_group_l = QVBoxLayout(settings_widget)
        settings = SettingsTabs()
        settings_group_l.addWidget(settings)
        settings_group_l.addWidget(
            QLabel("<i>{}</i>".format(t("gui.setting-descr", default="Hover the question mark icon to see setting description tooltip"))))

        buttons = QGroupBox(w)
        self.server_btn = QPushButton(self.start_ico, t("gui.b-start-server", default="Start server"))
        self.server_btn.clicked.connect(self.toggle_server)
        self.server_btn.setShortcut(Qt.CTRL | Qt.Key_S)

        #self.webclient_btn = QPushButton(self.start_ico, t("", default="Start webclient"))
        # self.webclient_btn.clicked.connect(self.toggle_client)
        # self.webclient_btn.setShortcut(Qt.CTRL|Qt.Key_W)

        open_client_btn = QPushButton(qta.icon("fa.external-link"), t("gui.b-open-webclient", default="Open Webclient"))
        open_client_btn.clicked.connect(self.open_client)
        open_client_btn.setShortcut(Qt.CTRL | Qt.Key_O)

        open_config_btn = QPushButton(qta.icon("fa.cogs"), t("gui.b-open-config", default="Open configuration"))
        open_config_btn.clicked.connect(self.open_cfg)
        open_config_btn.setShortcut(Qt.CTRL | Qt.Key_C)

        convert_btn = QPushButton(qta.icon("fa.refresh"), t("gui.b-hp-to-hpx", default="HP to HPX"))
        convert_btn.clicked.connect(self.convert_hp)

        for b in (self.server_btn, open_config_btn, convert_btn, open_client_btn):
            b.setFixedHeight(40)
        button_layout = QHBoxLayout(buttons)
        button_layout.addWidget(self.server_btn)
        button_layout.addWidget(open_client_btn)
        # button_layout.addWidget(self.webclient_btn)
        button_layout.addWidget(open_config_btn)
        button_layout.addWidget(convert_btn)

        infos = QGroupBox(t("gui.h-info", default="Info"))
        info_layout = QHBoxLayout(infos)
        version_layout = QFormLayout()
        version_layout.addRow(t("gui.t-server-version", default="Server version") +
                              ':', QLabel(".".join(str(x) for x in constants.version)))
        version_layout.addRow(t("gui.t-webclient-version", default="Webclient version") +
                              ':', QLabel(".".join(str(x) for x in constants.version_web)))
        version_layout.addRow(t("gui.t-database-version", default="Database version") +
                              ':', QLabel(".".join(str(x) for x in constants.version_db)))

        connect_layout = QFormLayout()
        server_addr_lbl = QLabel(config.host.value + ':' + str(config.port.value))
        config.host.add_trigger(lambda n, v: server_addr_lbl.setText(v + ':' + str(config.port.value)))
        config.port.add_trigger(lambda n, v: server_addr_lbl.setText(config.host.value + ':' + str(v)))
        config.host_web.add_trigger(lambda n, v: client_addr_lbl.setText(v + ':' + str(config.port.value)))
        config.port_web.add_trigger(lambda n, v: client_addr_lbl.setText(config.host.value + ':' + str(v)))

        client_addr_lbl = QLabel(config.host_web.value + ':' + str(config.port_web.value))

        connect_layout.addRow(t("gui.t-server", default="Server") + '@', server_addr_lbl)
        connect_layout.addRow(t("gui.t-webclient", default="Webclient") + '@', client_addr_lbl)
        info_layout.addLayout(connect_layout)
        info_layout.addLayout(version_layout)

        main_layout = QVBoxLayout(w)
        main_layout.addWidget(self.main_tab)
        main_layout.addWidget(infos)
        main_layout.addWidget(buttons)
        self.setCentralWidget(w)

        self.tray.setIcon(QIcon(constants.favicon_path))
        self.tray.activated.connect(self.tray_activated)
        tray_menu = QMenu()
        tray_menu.addAction(t("gui.t-show", default="Show"), lambda: all((self.showNormal(), self.activateWindow())))
        tray_menu.addSeparator()
        tray_menu.addAction(t("gui.t-quit", default="Quit"), lambda: self.real_close())
        self.tray.setContextMenu(tray_menu)

    def real_close(self):
        self.closing = True
        self.close()

    def force_close(self):
        self.forcing = True
        self.real_close()

    def tray_activated(self, reason):
        if reason != QSystemTrayIcon.Context:
            self.showNormal()
            self.activateWindow()

    def open_cfg(self):
        if not os.path.exists(constants.config_path):
            with open(constants.config_path, 'x'):
                pass
        io_cmd.CoreFS.open_with_default(constants.config_path)

    def convert_hp(self):
        c = ConvertHP(self)
        c.setWindowTitle(self.windowTitle())
        c.exec()

    def toggle_server(self, ecode=None):
        self.server_started = not self.server_started
        if ecode and ecode in (constants.ExitCode.Restart.value,
                               constants.ExitCode.Exit.value,
                               constants.ExitCode.Update.value,
                               ):
            global exitcode
            exitcode = ecode
            self.force_close()
        if self.server_started:
            self.server_btn.setText(t("gui.b-stop-server", default="Stop server"))
            self.server_btn.setIcon(self.stop_ico)
            self.server_process = self.start_server()
            self.activate_output.emit()
            if config.gui_open_webclient_on_server_start.value:
                Timer(4, self.open_client).start()
        else:
            self.force_kill = True
            self.server_btn.setText(t("gui.b-start-server", default="Start server"))
            self.server_btn.setIcon(self.start_ico)
            if self.server_process:
                self.stop_process(self.server_process)
                self.server_process = None

    def toggle_client(self, exitcode=None):
        self.client_started = not self.client_started
        if self.client_started:
            self.webclient_btn.setText(t("gui.b-stop-webclient", default="Stop webclient"))
            self.webclient_btn.setIcon(self.stop_ico)

        else:
            self.webclient_btn.setText(t("gui.b-start-webclient", default="Start webclient"))
            self.webclient_btn.setIcon(self.start_ico)

    def open_client(self):
        u = utils.get_qualified_name(config.host_web.value, config.port_web.value)
        if config.enable_ssl.value is True or config.enable_ssl.value == "web":
            p = "https://"
        else:
            p = "http://"
        webbrowser.open(p + u)

    def stop_process(self, p):
        if p:
            try:
                kill_proc_tree(p.pid)
                # p.kill()
            except psutil.NoSuchProcess:
                pass

    def watch_process(self, cb, p):
        p.join()
        if cb and not self.force_kill:
            cb(SQueueExit.get_nowait() if not p.exitcode else p.exitcode)
        else:
            self.force_kill = False

    def start_server(self):
        p = RedirectProcess(SQueue, SQueueExit, from_gui, target=main.start, name="gevent")
        p.start()
        Thread(target=self.watch_process, args=(self.toggle_server, p)).start()
        return p

    def changeEvent(self, ev):
        if ev.type() == QEvent.WindowStateChange:
            if self.windowState() == Qt.WindowMinimized:
                self.to_tray()
        return super().changeEvent(ev)

    def to_tray(self):
        self.tray.show()
        self.hide()

    def closeEvent(self, ev):
        if config.gui_minimize_on_close and not self.closing:
            self.to_tray()
            ev.ignore()
            return
        self.closing = False
        if not self.forcing and any((self.server_started, self.client_started)):
            if not self.isVisible():
                self.show()
            if QMessageBox.warning(self,
                                   self.windowTitle(),
                                   t("gui.t-still-running",
                                     default="Server or client is still running\nAre you sure you want to quit?"),
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)\
               == QMessageBox.No:
                ev.ignore()
                return
        [self.stop_process(x) for x in self.processes + [self.server_process, self.webclient_process]]
        super().closeEvent(ev)


def toggle_start_on_boot(node, value):
    if constants.is_frozen or constants.dev:
        app_path = os.path.abspath(constants.app_path)
        gui_name = constants.executable_gui_name
        if constants.is_osx:  # we're in Contents/MacOS, need to go two dir up
            app_path = pathlib.Path(app_path)
            app_path = os.path.join(*list(app_path.parts)[:-3])
            app_path = os.path.join(app_path, constants.osx_bundle_name)
        else:
            app_path = os.path.join(app_path, gui_name)

        name = "HappyPanda X GUI"
        if value:
            utils.add_to_startup(name, app_path)
        else:
            utils.remove_from_startup(name)


if __name__ == "__main__":

    SQueue = StreamQueue()
    SQueueExit = StreamQueue()

    utils.parse_options(utils.get_argparser().parse_args())

    utils.setup_i18n()
    if config.gui_start_on_boot.value:
        toggle_start_on_boot(None, config.gui_start_on_boot.value)
    config.gui_start_on_boot.add_trigger(toggle_start_on_boot)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setWindowIcon(QIcon(constants.favicon_path))
    app.setApplicationDisplayName("HappyPanda X")
    app.setApplicationName("HappyPanda X")
    app.setApplicationVersion(".".join(str(x) for x in constants.version))
    app.setOrganizationDomain("Twiddly")
    app.setOrganizationName("Twiddly")
    app.setDesktopFileName("HappyPanda X")
    window = Window()
    window.resize(650, 650)
    sys.stdout = SQueue
    sys.stderr = SQueue
    if config.gui_start_minimized.value:
        window.tray.show()
    else:
        window.show()
        window.activateWindow()
    e = app.exec()
    if exitcode == constants.ExitCode.Restart.value:
        utils.restart_process()
    elif exitcode == constants.ExitCode.Update.value:
        utils.launch_updater()
    sys.exit(e)

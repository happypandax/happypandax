import queue
import os
import threading
import random
import logging
import time
import scandir
import enum
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QDesktopWidget, QGroupBox,
                             QHBoxLayout, QFormLayout, QLabel, QLineEdit,
                             QPushButton, QProgressBar, QTextEdit, QComboBox,
                             QDateEdit, QFileDialog, QMessageBox, QScrollArea,
                             QCheckBox, QSizePolicy, QSpinBox, QDialog, QTabWidget,
                             QListView, QDialogButtonBox, QTableWidgetItem, QFrame,
                             QMenu, QStackedLayout, QToolBar)
from PyQt5.QtCore import (pyqtSignal, Qt, QPoint, QDate, QThread, QTimer, QSize)

from executors import Executors
import app_constants
import db_constants
import utils
import gallerydb
import fetch
import misc
import db

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class GalleryInfo(QWidget):
    def __init__(self, galleries, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self.galleries = galleries
        gallery_layout = QFormLayout(self)
        
        self._multiple_galleries = len(galleries) > 1

        def checkbox_layout(widget):
            if self._multiple_galleries:
                l = QHBoxLayout()
                l.addWidget(widget.g_check)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                l.addWidget(widget)
                return l
            else:
                widget.g_check.setChecked(True)
                widget.g_check.hide()
                return widget

        def add_check(widget):
            widget.g_check = QCheckBox(self)
            return widget

        self.title_edit = add_check(QLineEdit())
        self.author_edit = add_check(QLineEdit())
        #author_completer = misc.GCompleter(self, False, True, False)
        #author_completer.setCaseSensitivity(Qt.CaseInsensitive)
        #self.author_edit.setCompleter(author_completer)
        self.descr_edit = add_check(QTextEdit())
        self.descr_edit.setAcceptRichText(True)
        self.lang_box = add_check(QComboBox())
        self.lang_box.addItems(app_constants.G_LANGUAGES)
        self.lang_box.addItems(app_constants.G_CUSTOM_LANGUAGES)
        self.rating_box = add_check(QComboBox())
        self.rating_box.addItems([str(x) + " stars" if x != 1 else str(x) + " star" for x in range(6)])
        [self.rating_box.setItemData(x, x + 1) for x in range(5)]
        self._find_combobox_match(self.lang_box, app_constants.G_DEF_LANGUAGE, 0)
        tags_l = QVBoxLayout()
        tag_info = misc.ClickedLabel("How do i write namespace & tags? (hover)", parent=self)
        tag_info.setToolTip("Ways to write tags:\n\nNormal tags:\ntag1, tag2, tag3\n\n" + "Namespaced tags:\nns1:tag1, ns1:tag2\n\nNamespaced tags with one or more" + " tags under same namespace:\nns1:[tag1, tag2, tag3], ns2:[tag1, tag2]\n\n" + "Those three ways of writing namespace & tags can be combined freely.\n" + "Tags are seperated by a comma, NOT whitespace.\nNamespaces will be capitalized while tags" + " will be lowercased.")
        tag_info.setToolTipDuration(99999999)
        tags_l.addWidget(tag_info)
        self.tags_edit = add_check(misc.CompleterTextEdit())
        #self.tags_edit.setCompleter(misc.GCompleter(self, False, False))
        self.tags_edit.setPlaceholderText("Press Tab to autocomplete (Ctrl + E to show popup)")
        tags_l.addWidget(self.tags_edit)
        self.type_box = add_check(QComboBox())
        self.type_box.addItems(app_constants.G_TYPES)
        self._find_combobox_match(self.type_box, app_constants.G_DEF_TYPE, 0)
        self.pub_edit = add_check(QDateEdit())
        self.pub_edit.setCalendarPopup(True)
        self.pub_edit.setDate(QDate.currentDate())
        self.path_lbl = misc.ClickedLabel("")
        self.path_lbl.setWordWrap(True)
        self.path_lbl.clicked.connect(lambda a: utils.open_path(a, a) if a else None)

        self.link_box = add_check(QComboBox())
        
        rating_ = checkbox_layout(self.rating_box)
        lang_ = checkbox_layout(self.lang_box)
        if self._multiple_galleries:
            rating_.insertWidget(0, QLabel("Rating:"))
            lang_.addLayout(rating_)
            lang_l = lang_
        else:
            lang_l = QHBoxLayout()
            lang_l.addWidget(lang_)
            lang_l.addWidget(QLabel("Rating:"), 0, Qt.AlignRight)
            lang_l.addWidget(rating_)


        gallery_layout.addRow("Title:", checkbox_layout(self.title_edit))
        gallery_layout.addRow("Author:", checkbox_layout(self.author_edit))
        gallery_layout.addRow("Description:", checkbox_layout(self.descr_edit))
        gallery_layout.addRow("Language:", lang_l)
        gallery_layout.addRow("Tags:", tags_l)
        gallery_layout.addRow("Type:", checkbox_layout(self.type_box))
        gallery_layout.addRow("Publication Date:", checkbox_layout(self.pub_edit))
        gallery_layout.addRow("Path:", self.path_lbl)
        gallery_layout.addRow("Urls:", checkbox_layout(self.link_box))

        self.title_edit.setFocus()

        self.setGallery(galleries)

    def _find_combobox_match(self, combobox, key, default):
        f_index = combobox.findText(key, Qt.MatchFixedString)
        if f_index != -1:
            combobox.setCurrentIndex(f_index)
            return True
        else:
            combobox.setCurrentIndex(default)
            return False

    def setGallery(self, galleries):
        "To be used for when editing a gallery"

        if len(galleries) == 1:
            gallery = galleries[0]

            self.descr_edit.setText(gallery.info)

            self.tags_edit.setText(gallery.tags_to_string())

            self._find_combobox_match(self.rating_box, self.rating_box.itemText(gallery.rating), 0)
            if not self._find_combobox_match(self.lang_box, gallery.language.name, 1):
                self._find_combobox_match(self.lang_box, app_constants.G_DEF_LANGUAGE, 1)
            if not self._find_combobox_match(self.type_box, gallery.type, 0):
                self._find_combobox_match(self.type_box, app_constants.G_DEF_TYPE, 0)

            gallery_pub_date = "{}".format(gallery.pub_date).split(' ')
            try:
                self.gallery_time = datetime.strptime(gallery_pub_date[1], '%H:%M:%S').time()
            except IndexError:
                pass
            qdate_pub_date = QDate.fromString(gallery_pub_date[0], "yyyy-MM-dd")
            self.pub_edit.setDate(qdate_pub_date)

            self.path_lbl.setText(gallery.path)

        else:
            g = galleries[0]
            if all(map(lambda x: x.info == g.info, galleries)):
                self.descr_edit.setText(g.info)
                self.descr_edit.g_check.setChecked(True)
            if all(map(lambda x: x.tags == g.tags, galleries)):
                self.tags_edit.setText(g.tags_to_string())
                self.tags_edit.g_check.setChecked(True)
            if all(map(lambda x: x.language == g.language, galleries)):
                if not self._find_combobox_match(self.lang_box, g.language.name, 1):
                    self._find_combobox_match(self.lang_box, app_constants.G_DEF_LANGUAGE, 1)
                self.lang_box.g_check.setChecked(True)
            if all(map(lambda x: x.rating == g.rating, galleries)):
                self._find_combobox_match(self.rating_box, self.rating_box.itemText(g.rating), 0)
                self.rating_box.g_check.setChecked(True)
            if all(map(lambda x: x.type == g.type, galleries)):
                if not self._find_combobox_match(self.type_box, g.type, 0):
                    self._find_combobox_match(self.type_box, app_constants.G_DEF_TYPE, 0)
                self.type_box.g_check.setChecked(True)
            if all(map(lambda x: x.pub_date == g.pub_date, galleries)):
                gallery_pub_date = "{}".format(g.pub_date).split(' ')
                try:
                    self.gallery_time = datetime.strptime(gallery_pub_date[1], '%H:%M:%S').time()
                except IndexError:
                    pass
                qdate_pub_date = QDate.fromString(gallery_pub_date[0], "yyyy-MM-dd")
                self.pub_edit.setDate(qdate_pub_date)
                self.pub_edit.g_check.setChecked(True)

class GalleryDialog(QDialog):
    """
    A window for modifying gallery.
    Pass a list of galleries or a gallery
    """

    def __init__(self, galleries, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAutoFillBackground(True)
        self.parent_widget = parent
        main_layout = QVBoxLayout(self)

        self.tabwidget = QTabWidget(self)
        #self.tabwidget.addTab(MiscItems(), "&Misc ")

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        main_layout.addWidget(self.tabwidget)
        main_layout.addWidget(buttonbox)
        self._multiple_galleries = False

        if not isinstance(galleries, list):
            galleries = [galleries]

        if len(galleries) == 1:
            self.setWindowTitle('Edit gallery')
        else:
            self._multiple_galleries = True
            self.setWindowTitle('Edit {} galleries'.format(len(galleries)))

        self.tabwidget.addTab(GalleryInfo(galleries, self), "&Gallery Info")
        if self._multiple_galleries:
            self.resize(500, 400)
        else:
            self.resize(500, 600)

    def reject(self):
        self.close()

    def accept(self):
        return True

class GalleryEditMenu(QMenu):
    remove = pyqtSignal(list)

    def __init__(self, items, parent):
        super().__init__(parent)
        self.items = items
        self.parent_widget = parent
        self.addAction("Edit", self.edit_dialog)
        self.addAction("Remove from list", lambda: self.remove.emit(items))

    def edit_dialog(self):
        galleries = [item.data(app_constants.ITEM_ROLE) for item in self.items]
        gdialog = GalleryDialog(galleries, self.parent_widget)
        gdialog.exec()

class Item(QWidget):
    def __init__(self, gallery):
        super().__init__()
        assert isinstance(gallery, db.Gallery)
        mainlayout = QHBoxLayout(self)
        self.profile = QLabel(self)
        self.profile.setFixedWidth(50)
        mainlayout.addWidget(self.profile)

        rightlayout = QVBoxLayout()
        mainlayout.addLayout(rightlayout)

        self.title = QLabel(gallery.title, self)
        self.title.setWordWrap(True)
        if gallery.in_archive:
            self.path = QLabel("In archive: {}".format(gallery.path), self)
        else:
            self.path = QLabel(gallery.path, self)
        self.path.setWordWrap(True)
        rightlayout.addWidget(self.title)
        rightlayout.addWidget(self.path)
        self.setFixedHeight(100)


class ItemList(misc.DefaultTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setIconSize(QSize(20, 20))
        self.setHorizontalHeaderLabels(['Status', 'Gallery'])
        self.horizontalHeader().setSectionResizeMode(0, self.horizontalHeader().ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        v_header = self.verticalHeader()
        v_header.hide()

    def add_item(self, col1item, col2item):
        assert isinstance(col1item, QTableWidgetItem)
        assert isinstance(col2item, QTableWidgetItem)
        self.insertRow(0)
        self.setItem(0, 0, col1item)
        self.setItem(0, 1, col2item)
        self.resizeColumnToContents(0)

    def contextMenuEvent(self, ev):
        
        items = self.selectedItems()
        
        if items:
            menu = GalleryEditMenu(items, self)
            menu.exec(ev.globalPos())
            ev.accept()
        else:
            ev.ignore()

class ItemsBase(QWidget):
    def __init__(self, parent, *args):
        super().__init__(parent, *args)

    def accept(self):
        return True

class GalleryManager(ItemsBase):
    from_path = pyqtSignal(str, tuple)
    scan_path = pyqtSignal(str, tuple)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Dialog)
        self._thread = QThread(self)
        self._thread.start()
        self._scan_proc_running = 0
        self.session = db_constants.SESSION()
        self.scan = fetch.GalleryScan()
        def _reset_scan_proc():
            self._scan_proc_running -= 1
            if not self._scan_proc_running:
                self.add_progress.hide()
        self.scan.finished.connect(_reset_scan_proc)

        self.scan.moveToThread(self._thread)
        self.scan.scan_finished.connect(self.toggle_progress)
        self.scan.galleryitem.connect(self.add_scanitem)
        self.scan_path.connect(self.scan.scan_path)
        self.from_path.connect(self.scan.from_path)

        main_layout = QVBoxLayout(self)
        
        add_box = QGroupBox("Add Gallery", self)
        main_layout.addWidget(add_box)
        add_box_main_l = QVBoxLayout(add_box)
        add_box_l = QHBoxLayout()
        add_box_main_l.addLayout(add_box_l)
        add_box_l.setAlignment(Qt.AlignLeft)
        add_gallery_group = QGroupBox(self)
        add_gallery_l = QHBoxLayout(add_gallery_group)
        from_folder = QPushButton(app_constants.PLUS_ICON, "Add loose folder")
        from_folder.clicked.connect(lambda: self.file_or_folder('f'))
        from_archive = QPushButton(app_constants.PLUS_ICON, "Add archives")
        from_archive.clicked.connect(lambda: self.file_or_folder('a'))
        misc.fixed_widget_size(from_archive)
        misc.fixed_widget_size(from_folder)
        add_gallery_l.addWidget(from_archive)
        add_gallery_l.addWidget(from_folder)
        self.populate_group = QGroupBox(self)
        populate_group_l = QHBoxLayout(self.populate_group)
        populate_folder = QPushButton(app_constants.PLUS_ICON, "Populate from folder")
        populate_folder.clicked.connect(lambda: self.file_or_folder('f', True))
        misc.fixed_widget_size(populate_folder)
        populate_group_l.addWidget(populate_folder)
        self.same_namespace = QCheckBox("Put folders and/or archives in same namespace", self)
        self.skip_existing = QCheckBox("Skip already existing galleries", self)
        progress_l = QHBoxLayout()
        self.add_progress = QProgressBar()
        self.add_progress.setMaximum(0)
        self.add_progress.setMinimum(0)
        self.add_progress.hide()
        progress_l.addWidget(self.skip_existing)
        progress_l.addWidget(self.add_progress)
        populate_group_l.addWidget(self.same_namespace)
        add_box_l.addWidget(add_gallery_group)
        self.populate_progress = QProgressBar(self)
        self.populate_progress.setMaximum(0)
        add_box_l.addWidget(self.populate_progress)
        self.populate_progress.hide()
        add_box_l.addWidget(self.populate_group)
        add_box_main_l.addLayout(progress_l)

        self.item_list = ItemList(self)
        self.item_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        main_layout.addWidget(self.item_list, 2)

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.close)

        main_layout.addWidget(buttonbox)
        self.setWindowTitle("Addition Manager")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(700, 700)
        self.show()

    def toggle_progress(self):
        if self.populate_progress.isVisible():
            self.populate_progress.hide()
            self.populate_group.show()
        else:
            self.populate_group.hide()
            self.populate_progress.show()

    def file_or_folder(self, mode, scan=False):
        """
        Pass which mode to open the folder explorer in:
        'f': directory
        'a': files
        Or pass a predefined path
        """
        name = None
        if mode == 'a':
            name = QFileDialog.getOpenFileNames(self, 'Choose archive(s)',
                                              filter=utils.FILE_FILTER)
            name = name[0]
        elif mode == 'f':
            name = QFileDialog.getExistingDirectory(self, 'Choose loose folder')
        elif mode:
            if os.path.exists(mode):
                name = mode
            else:
                return None
        if not name:
            return
        if scan:
            self.toggle_progress()
            self.scan_path.emit(name, tuple())
            self._scan_proc_running += 1
        else:
            if not isinstance(name, list):
                name = [name]
            for n in name:
                self.from_path.emit(n, tuple())
                #self.scan.from_path(n, tuple())
                self._scan_proc_running += 1
        self.add_progress.show()

    def add_scanitem(self, item):
        assert isinstance(item, fetch.GalleryScanItem)
        t_item = QTableWidgetItem()
        icon = app_constants.CHECK_ICON
        if item.error:
            icon = app_constants.CROSS_RED_ICON
        if item.gallery:
            t_item.setText(item.gallery.title.name)
            t_item.setData(app_constants.ITEM_ROLE, item.gallery)
        else:
            t_item.setText("Failed adding gallery: {}".format(item.string_error()))

        self.item_list.add_item(QTableWidgetItem(icon, ''), t_item)

    def accept(self):
        ""
        if self._scan_proc_running:
            msg = QMessageBox(QMessageBox.Information, "Are you sure?",
                              "Scan is still in process.\nAre you sure you want to close?",
                              QMessageBox.Yes | QMessageBox.No)
            if msg.exec() == msg.No:
                return False
        galleries = []

        r = 0
        it = self.item_list.item(r, 1)
        while it:
            r += 1
            g = it.data(app_constants.ITEM_ROLE)
            if g:
                galleries.append(g)
            it = self.item_list.item(r, 1)

        Executors.add_gallery(galleries)
        self.hide()


class GalleryMetadataWidget(QWidget):
    up = pyqtSignal(object)
    down = pyqtSignal(object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0,0,0,0)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        self.checkbox = QCheckBox()
        self.label = QLabel("E-Hentai")
        self.label.setAlignment(Qt.AlignLeft)
        up_btn = QPushButton(app_constants.ARROW_UP_ICON, '')
        misc.fixed_widget_size(up_btn)
        up_btn.clicked.connect(self.up.emit)
        down_btn = QPushButton(app_constants.ARROW_DOWN_ICON, '')
        down_btn.clicked.connect(self.down.emit)
        misc.fixed_widget_size(down_btn)
        h_l = QHBoxLayout()
        h_l.setSpacing(0)
        h_l.addWidget(self.checkbox)
        h_l.addWidget(self.label, 0, Qt.AlignLeft)
        h_l.addWidget(up_btn)
        h_l.addWidget(down_btn)
        main_layout.addLayout(h_l)
        main_layout.addWidget(misc.Line("h"))

class GalleryMetadataItems(ItemsBase):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        
        settings_l = QVBoxLayout()
        settings_l.setSpacing(0)

        metadata_group = QGroupBox("Metadata Providers", self)
        metadata_group_l = QVBoxLayout(metadata_group)
        metadata_group_l.setSpacing(0)
        for x in range(3):
            metadata_group_l.addWidget(GalleryMetadataWidget(self))
        settings_l.addWidget(metadata_group)

        settings_btn_l = QHBoxLayout()
        settings_btn_l.setAlignment(Qt.AlignRight)
        settings_l.addLayout(settings_btn_l)
        main_layout.addLayout(settings_l)
        fetch_btn = QPushButton("Fetch")
        misc.fixed_widget_size(fetch_btn)
        self.auto_fetch = QCheckBox("Start fetching automatically", self)
        settings_btn_l.addWidget(self.auto_fetch, 0, Qt.AlignLeft)
        settings_btn_l.addWidget(fetch_btn, 0, Qt.AlignRight)

        self.item_list = ItemList(self)
        self.item_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        main_layout.addWidget(self.item_list, 2)

class GalleryTypeWidget(QFrame):
    remove = pyqtSignal(object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(self.StyledPanel)
        main_layout = QFormLayout(self)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Name")
        self.color = QLineEdit()
        self.color.setPlaceholderText("Color")
        main_layout.addRow(self.name, self.color)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, ev):
        if ev.button() & Qt.LeftButton:
            self.remove.emit(self)
        return super().mousePressEvent(ev)

class MiscItems(ItemsBase):
    STATUS = set()
    LANGUAGE = set()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        add_gtype = QGroupBox("Gallery Type", self)
        main_layout.addWidget(add_gtype)
        add_gtype_l = QVBoxLayout(add_gtype)
        self.new_gtype = QPushButton(app_constants.PLUS_ICON, "New Gallery Type")
        misc.fixed_widget_size(self.new_gtype)
        self.new_gtype.clicked.connect(self.add_gtype)
        add_gtype_l.addWidget(self.new_gtype)
        self.gtypes = misc.FlowLayout()
        add_gtype_l.addLayout(self.gtypes)


    def accept(self):
        return super().accept()

class MetadataManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Dialog)
        main_layout = QVBoxLayout(self)

        self.tabwidget = QTabWidget(self)
        self.tabwidget.addTab(GalleryMetadataItems(), "&Queue")

        main_layout.addWidget(self.tabwidget)
        self.setWindowTitle("Metadata Manager")
        self.resize(700, 700)

    def closeEvent(self, event):
        self.hide()


class ContextBar(QWidget):
    
    class Context(enum.Enum):
        Collection = 1
        Gallery = 2
        Page = 3

    class CollectionBar(QToolBar):

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setIconSize(QSize(15, 15))
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)


    class GalleryBar(QToolBar):

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setIconSize(QSize(15, 15))
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            new_gtype = self.addAction(app_constants.PLUS_ICON, "Gallery Types", self.gtypes)
            new_status = self.addAction(app_constants.PLUS_ICON, "Gallery Status", self.gstatus)
            new_lang = self.addAction(app_constants.PLUS_ICON, "Languages", self.glanguage)

        def new_dialog(self, title, accept=None):
            dia = QDialog(self)
            dia.resize(300, 300)
            dia.setWindowTitle(title)
            l = QVBoxLayout(dia)
            dia_l = QFormLayout(dia)
            l.addLayout(dia_l)
            buttonbox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Close)
            buttonbox.accepted.connect(accept if accept else dia.accept)
            buttonbox.rejected.connect(dia.reject)
            l.addWidget(buttonbox)
            return dia, dia_l

        def glanguage(self):
            dia, dia_l = self.new_dialog("Languages")
            languages = misc.FlowLayout()
            new_language = QLineEdit(self)
            def rem_l(w):
                lang = w.language
                msg = QMessageBox(QMessageBox.Warning, "Are you sure?",
                                    "Some galleries may have a reference to this language.\nAre you sure you want to delete?",
                                    QMessageBox.Yes|QMessageBox.No, parent=self)
                if msg.exec() == QMessageBox.No:
                    return
                lang.delete().commit()
                languages.removeWidget(w)
                w.setParent(None)

            def add_l():
                txt = new_language.text()
                if txt:
                    new_language.clear()
                    lang = db.Language()
                    lang.name = txt
                    lang = lang.exists(True)
                    if not lang.id:
                        tagtxt = misc.TagText(txt)
                        tagtxt.language = lang
                        tagtxt.clicked.connect(lambda: rem_l(tagtxt))
                        languages.addWidget(tagtxt)
                        sess = db_constants.SESSION()
                        sess.add(lang)
                        sess.commit()

            new_language.setPlaceholderText("New language name")
            add_btn = QPushButton("Add")
            add_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            add_btn.clicked.connect(add_l)
            lang_l = QHBoxLayout()
            lang_l.addWidget(new_language)
            lang_l.addWidget(add_btn)
            dia_l.addRow(lang_l)
            dia_l.addRow(languages)
            for l in db_constants.SESSION().query(db.Language).all():
                w = misc.TagText(l.name)
                w.clicked.connect(lambda: rem_l(w))
                w.language = l
                languages.addWidget(w)
            dia.exec()

        def gstatus(self):
            dia, dia_l = self.new_dialog("Gallery Status")
            status = misc.FlowLayout()
            new_status = QLineEdit(self)

            def rem(w):
                stat = w.status
                msg = QMessageBox(QMessageBox.Warning, "Are you sure?",
                                    "Some gallery namespaces may have a reference to this status.\nAre you sure you want to delete?",
                                    QMessageBox.Yes|QMessageBox.No, parent=self)
                if msg.exec() == QMessageBox.No:
                    return
                stat.delete().commit()
                status.removeWidget(w)
                w.setParent(None)

            def add():
                txt = new_status.text()
                if txt:
                    new_status.clear()
                    stat = db.Status()
                    stat.name = txt
                    stat = stat.exists(True)
                    if not stat.id:
                        tagtxt = misc.TagText(txt)
                        tagtxt.status = stat
                        tagtxt.clicked.connect(lambda: rem(tagtxt))
                        status.addWidget(tagtxt)
                        sess = db_constants.SESSION()
                        sess.add(stat)
                        sess.commit()

            new_status.setPlaceholderText("New status name")
            add_btn = QPushButton("Add")
            add_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            add_btn.clicked.connect(add)
            hoz_l = QHBoxLayout()
            hoz_l.addWidget(new_status)
            hoz_l.addWidget(add_btn)
            dia_l.addRow(hoz_l)
            dia_l.addRow(status)

            for i in db_constants.SESSION().query(db.Status).all():
                w = misc.TagText(i.name)
                w.clicked.connect(lambda: rem(w))
                w.status = i
                status.addWidget(w)
            dia.exec()

        def gtypes(self):
            dia, dia_l = self.new_dialog("Gallery Types")
            types = misc.FlowLayout()
            new_gtype = QLineEdit(self)

            def rem(w):
                gtype = w.gtype
                msg = QMessageBox(QMessageBox.Warning, "Are you sure?",
                                    "Some galleries may have a reference to this type.\nAre you sure you want to delete?",
                                    QMessageBox.Yes|QMessageBox.No, parent=self)
                if msg.exec() == QMessageBox.No:
                    return
                gtype.delete().commit()
                types.removeWidget(w)
                w.setParent(None)

            def add():
                txt = new_gtype.text().capitalize()
                if txt:
                    new_gtype.clear()
                    gtype = db.GalleryType()
                    gtype.name = txt
                    gtype = gtype.exists(True)
                    if not gtype.id:
                        tagtxt = misc.TagText(txt)
                        tagtxt.gtype = gtype
                        tagtxt.clicked.connect(lambda: rem(tagtxt))
                        types.addWidget(tagtxt)
                        sess = db_constants.SESSION()
                        sess.add(gtype)
                        sess.commit()

            new_gtype.setPlaceholderText("New gallery type name")
            add_btn = QPushButton("Add")
            add_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            add_btn.clicked.connect(add)
            hoz_l = QHBoxLayout()
            hoz_l.addWidget(new_gtype)
            hoz_l.addWidget(add_btn)
            dia_l.addRow(hoz_l)
            dia_l.addRow(types)

            for i in db_constants.SESSION().query(db.GalleryType).all():
                w = misc.TagText(i.name)
                w.clicked.connect(lambda: rem(w))
                w.gtype = i
                types.addWidget(w)
            dia.exec()

    class PageBar(QToolBar):

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setIconSize(QSize(15, 15))
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setContentsMargins(0,0,0,0)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0,0,0,0)
        self._layout.setSpacing(0)
        self._layout.setSizeConstraint(self._layout.SetNoConstraint)
        self.handle = misc.ArrowHandle(Qt.Horizontal, self)
        self._layout.addWidget(self.handle)
        self.stack_layout = QStackedLayout()
        self.stack_layout.setContentsMargins(0,0,0,0)
        self.stack_layout.setSpacing(0)
        self._layout.addLayout(self.stack_layout)
        
        self.collection_idx = self.stack_layout.addWidget(self.CollectionBar(self))
        self.gallery_idx = self.stack_layout.addWidget(self.GalleryBar(self))
        self.page_idx = self.stack_layout.addWidget(self.PageBar(self))

    def setContext(self, ctx):
        ""
        assert isinstance(ctx, self.Context)

        if ctx == self.Context.Collection:
            self.stack_layout.setCurrentIndex(self.collection_idx)
        elif ctx == self.Context.Gallery:
            self.stack_layout.setCurrentIndex(self.gallery_idx)
        elif ctx == self.Context.Page:
            self.stack_layout.setCurrentIndex(self.page_idx)







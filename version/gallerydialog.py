import queue, os, threading, random, logging, time, scandir
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QDesktopWidget, QGroupBox,
                             QHBoxLayout, QFormLayout, QLabel, QLineEdit,
                             QPushButton, QProgressBar, QTextEdit, QComboBox,
                             QDateEdit, QFileDialog, QMessageBox, QScrollArea,
                             QCheckBox, QSizePolicy, QSpinBox, QDialog, QTabWidget,
                             QListView, QDialogButtonBox, QTableWidgetItem, QFrame,
                             QMenu)
from PyQt5.QtCore import (pyqtSignal, Qt, QPoint, QDate, QThread, QTimer, QSize)

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
        self.rating_box.addItems([str(x)+" stars" if x != 1 else " star" for x in range(5, 1)])
        [self.rating_box.setItemData(x, x+1) for x in range(5)]
        self._find_combobox_match(self.lang_box, app_constants.G_DEF_LANGUAGE, 0)
        tags_l = QVBoxLayout()
        tag_info = misc.ClickedLabel("How do i write namespace & tags? (hover)", parent=self)
        tag_info.setToolTip("Ways to write tags:\n\nNormal tags:\ntag1, tag2, tag3\n\n"+
                      "Namespaced tags:\nns1:tag1, ns1:tag2\n\nNamespaced tags with one or more"+
                      " tags under same namespace:\nns1:[tag1, tag2, tag3], ns2:[tag1, tag2]\n\n"+
                      "Those three ways of writing namespace & tags can be combined freely.\n"+
                      "Tags are seperated by a comma, NOT whitespace.\nNamespaces will be capitalized while tags"+
                      " will be lowercased.")
        tag_info.setToolTipDuration(99999999)
        tags_l.addWidget(tag_info)
        self.tags_edit = add_check(misc.CompleterTextEdit())
        self.tags_edit.setCompleter(misc.GCompleter(self, False, False))
        self.tags_edit.setPlaceholderText("Press Tab to autocomplete (Ctrl + E to show popup)")
        self.type_box = add_check(QComboBox())
        self.type_box.addItems(app_constants.G_TYPES)
        self._find_combobox_match(self.type_box, app_constants.G_DEF_TYPE, 0)
        self.status_box = add_check(QComboBox())
        self.status_box.addItems(app_constants.G_STATUS)
        self._find_combobox_match(self.status_box, app_constants.G_DEF_STATUS, 0)
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

            self.tags_edit.setText(utils.tag_to_string(gallery.tags.all()))


            if not self._find_combobox_match(self.lang_box, gallery.language, 1):
                self._find_combobox_match(self.lang_box, app_constants.G_DEF_LANGUAGE, 1)
            if not self._find_combobox_match(self.type_box, gallery.type, 0):
                self._find_combobox_match(self.type_box, app_constants.G_DEF_TYPE, 0)
            if not self._find_combobox_match(self.status_box, gallery.status, 0):
                self._find_combobox_match(self.status_box, app_constants.G_DEF_STATUS, 0)

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
                self.tags_edit.setText(utils.tag_to_string(g.tags.all()))
                self.tags_edit.g_check.setChecked(True)
            if all(map(lambda x: x.language == g.language, galleries)):
                if not self._find_combobox_match(self.lang_box, g.language, 1):
                    self._find_combobox_match(self.lang_box, app_constants.G_DEF_LANGUAGE, 1)
                self.lang_box.g_check.setChecked(True)
            if all(map(lambda x: x.rating == g.rating, galleries)):
                self.rating_box.setValue(g.rating)
                self.rating_box.g_check.setChecked(True)
            if all(map(lambda x: x.type == g.type, galleries)):
                if not self._find_combobox_match(self.type_box, g.type, 0):
                    self._find_combobox_match(self.type_box, app_constants.G_DEF_TYPE, 0)
                self.type_box.g_check.setChecked(True)
            if all(map(lambda x: x.status == g.status, galleries)):
                if not self._find_combobox_match(self.status_box, g.status, 0):
                    self._find_combobox_match(self.status_box, app_constants.G_DEF_STATUS, 0)
                self.status_box.g_check.setChecked(True)
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
        self.setLayout(m_l)
        if self._multiple_galleries:
            self.resize(500, 400)
        else:
            self.resize(500, 600)

    def reject(self):
        self.close()

    def accept(self):
        pass

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
        self.setHorizontalHeaderLabels(
	        ['Status', 'Gallery'])
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
    def __init__(self, parent=None):
        super().__init__(parent)

    def items(self):
        return

class GalleryAddItems(ItemsBase):
    from_path = pyqtSignal(str, tuple)
    scan_path = pyqtSignal(str, tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = QThread(self)
        self._thread.start()
        self.session = db_constants.SESSION()
        self.scan = fetch.GalleryScan()

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
        populate_group_l.addWidget(self.same_namespace)
        add_box_l.addWidget(add_gallery_group)
        self.populate_progress = QProgressBar(self)
        self.populate_progress.setMaximum(0)
        add_box_l.addWidget(self.populate_progress)
        self.populate_progress.hide()
        add_box_l.addWidget(self.populate_group)
        add_box_main_l.addWidget(self.skip_existing)

        self.item_list = ItemList(self)
        self.item_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        main_layout.addWidget(self.item_list, 2)

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
        else:
            if not isinstance(name, list):
                name = [name]
            for n in name:
                self.from_path.emit(n, tuple())

    def closeEvent(self, ev):
        self._thread.exit()
        self._thread.deleteLater()
        return super().closeEvent(ev)

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

    def items(self):
        print(self.item_list.columnAt(1))
       

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
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        
        add_collection = QGroupBox("Add Collection", self)
        main_layout.addWidget(add_collection)
        add_collection_l = QFormLayout(add_collection)
        add_collection_l.setAlignment(Qt.AlignLeft)
        self.collection_name = QLineEdit(self)
        self.collection_name.setPlaceholderText("New collection name...")
        self.collection_cover = misc.PathLineEdit(self)
        self.collection_info = QTextEdit(self)
        self.collection_info.setAcceptRichText(True)
        new_collection = QPushButton(app_constants.PLUS_ICON, "New Collection")
        misc.fixed_widget_size(new_collection)
        add_collection_l.addRow("Name:", self.collection_name)
        add_collection_l.addRow("Cover:", self.collection_cover)
        add_collection_l.addRow("Description:", self.collection_info)
        add_collection_l.addRow(new_collection)

        add_gtype = QGroupBox("Gallery Type", self)
        main_layout.addWidget(add_gtype)
        add_gtype_l = QVBoxLayout(add_gtype)
        self.new_gtype = QPushButton(app_constants.PLUS_ICON, "New Gallery Type")
        misc.fixed_widget_size(self.new_gtype)
        self.new_gtype.clicked.connect(self.add_gtype)
        add_gtype_l.addWidget(self.new_gtype)
        self.gtypes = misc.FlowLayout()
        add_gtype_l.addLayout(self.gtypes)

        add_language = QGroupBox("Language", self)
        main_layout.addWidget(add_language)
        add_language_l = QVBoxLayout(add_language)
        self.new_language = QLineEdit(self)
        self.new_language.returnPressed.connect(self.add_language)
        self.new_language.setPlaceholderText("New language (Click to remove)")
        add_language_l.addWidget(self.new_language)
        self.languages = misc.FlowLayout()
        add_language_l.addLayout(self.languages)

        add_status = QGroupBox("Status", self)
        main_layout.addWidget(add_status)
        add_status_l = QVBoxLayout(add_status)
        self.new_status = QLineEdit(self)
        self.new_status.returnPressed.connect(self.add_status)
        self.new_status.setPlaceholderText("New status (Click to remove)")
        add_status_l.addWidget(self.new_status)
        self.status = misc.FlowLayout()
        add_status_l.addLayout(self.status)

    def add_gtype(self):
        gtype = GalleryTypeWidget(self)
        gtype.remove.connect(self.remove_gtype)
        self.gtypes.addWidget(gtype)

    def remove_gtype(self, widget):
        self.gtypes.removeWidget(widget)
        widget.setParent(None)

    def add_language(self):
        lang = self.new_language.text()
        self.new_language.clear()
        lang_btn = misc.TagText(lang)
        lang_btn.clicked.connect(lambda: self.remove_language(lang_btn))
        self.languages.addWidget(lang_btn)

    def remove_language(self, widget):
        self.languages.removeWidget(widget)
        widget.setParent(None)

    def add_status(self):
        status = self.new_status.text()
        self.new_status.clear()
        status_btn = misc.TagText(status)
        status_btn.clicked.connect(lambda: self.remove_language(status_btn))
        self.status.addWidget(status_btn)

    def remove_status(self, widget):
        self.status.removeWidget(widget)
        widget.setParent(None)


class ItemManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Dialog)
        main_layout = QVBoxLayout(self)

        self.tabwidget = QTabWidget(self)
        self.tabwidget.addTab(GalleryAddItems(), "&Gallery")
        self.tabwidget.addTab(MiscItems(), "&Misc")

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.close)

        main_layout.addWidget(self.tabwidget)
        main_layout.addWidget(buttonbox)
        self.setWindowTitle("Addition Manager")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(700, 700)
        self.show()
        
    def accept(self):
        pass


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
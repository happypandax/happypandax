import logging

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QListWidget, QWidget,
							 QListWidgetItem, QStackedLayout, QPushButton,
							 QLabel, QTabWidget, QLineEdit, QGroupBox, QFormLayout,
							 QCheckBox, QRadioButton, QSpinBox, QSizePolicy,
							 QScrollArea, QFontDialog)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPalette, QPixmapCache

from misc import FlowLayout, Spacer, PathLineEdit
import settings
import gui_constants

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class SettingsDialog(QWidget):
	"A settings dialog"
	scroll_speed_changed = pyqtSignal()
	def __init__(self, parent=None):
		super().__init__(parent, flags=Qt.Window)
		self.resize(700, 500)
		self.show()
		self.restore_values()
		self.initUI()

	def initUI(self):
		main_layout = QVBoxLayout()
		sub_layout = QHBoxLayout()
		# Left Panel
		left_panel = QListWidget()
		left_panel.setViewMode(left_panel.ListMode)
		#left_panel.setIconSize(QSize(40,40))
		left_panel.setTextElideMode(Qt.ElideRight)
		left_panel.setMaximumWidth(200)
		left_panel.itemClicked.connect(self.change)
		#web.setText('Web')
		self.application = QListWidgetItem()
		self.application.setText('Application')
		self.web = QListWidgetItem()
		self.web.setText('Web')
		self.visual = QListWidgetItem()
		self.visual.setText('Visual')
		self.advanced = QListWidgetItem()
		self.advanced.setText('Advanced')
		self.about = QListWidgetItem()
		self.about.setText('About')

		#main.setIcon(QIcon(os.path.join(gui_constants.static_dir, 'plus2.png')))
		left_panel.addItem(self.application)
		left_panel.addItem(self.web)
		left_panel.addItem(self.visual)
		left_panel.addItem(self.advanced)
		left_panel.addItem(self.about)
		left_panel.setMaximumWidth(100)

		# right panel
		self.right_panel = QStackedLayout()
		self.init_right_panel()

		# bottom
		bottom_layout = QHBoxLayout()
		ok_btn = QPushButton('Ok')
		ok_btn.clicked.connect(self.accept)
		cancel_btn = QPushButton('Cancel')
		cancel_btn.clicked.connect(self.close)
		info_lbl = QLabel()
		info_lbl.setText('<a href="https://github.com/Pewpews/happypanda">'+
				   'Visit GitHub Repo</a> | Options marked with * requires application restart.')
		info_lbl.setTextFormat(Qt.RichText)
		info_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
		info_lbl.setOpenExternalLinks(True)
		self.spacer = QWidget()
		self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		bottom_layout.addWidget(info_lbl, 0, Qt.AlignLeft)
		bottom_layout.addWidget(self.spacer)
		bottom_layout.addWidget(ok_btn, 0, Qt.AlignRight)
		bottom_layout.addWidget(cancel_btn, 0, Qt.AlignRight)

		sub_layout.addWidget(left_panel)
		sub_layout.addLayout(self.right_panel)
		main_layout.addLayout(sub_layout)
		main_layout.addLayout(bottom_layout)

		self.restore_options()

		self.setLayout(main_layout)
		self.setWindowTitle('Settings')


	def change(self, item):
		def curr_index(index):
			if index != self.right_panel.currentIndex():
				self.right_panel.setCurrentIndex(index)
		if item == self.application:
			curr_index(self.application_index)
		elif item == self.web:
			curr_index(self.web_index)
		elif item == self.visual:
			curr_index(self.visual_index)
		elif item == self.advanced:
			curr_index(self.advanced_index)
		elif item == self.about:
			curr_index(self.about_index)

	def restore_values(self):
		#Web
		self.exprops = settings.ExProperties()

		# Visual
		self.high_quality_thumbs = gui_constants.HIGH_QUALITY_THUMBS
		self.popup_width = gui_constants.POPUP_WIDTH
		self.popup_height = gui_constants.POPUP_HEIGHT
		self.style_sheet = gui_constants.user_stylesheet_path

		# Advanced
		self.scroll_speed = gui_constants.SCROLL_SPEED
		self.cache_size = gui_constants.THUMBNAIL_CACHE_SIZE
		self.prefetch_item_amnt = gui_constants.PREFETCH_ITEM_AMOUNT

	def restore_options(self):
		# App / Monitor / Misc
		self.enable_monitor.setChecked(gui_constants.ENABLE_MONITOR)
		self.look_new_gallery_startup.setChecked(gui_constants.LOOK_NEW_GALLERY_STARTUP)
		self.auto_add_new_galleries.setChecked(gui_constants.LOOK_NEW_GALLERY_AUTOADD)
		# App / Monitor / Folders
		for path in gui_constants.MONITOR_PATHS:
			self.add_folder_monitor(path)

		# Web / General
		if 'g.e-hentai' in gui_constants.DEFAULT_EHEN_URL:
			self.default_ehen_url.setChecked(True)
		else:
			self.exhentai_ehen_url.setChecked(True)
		
		self.replace_metadata.setChecked(gui_constants.REPLACE_METADATA)
		self.always_first_hit.setChecked(gui_constants.ALWAYS_CHOOSE_FIRST_HIT)
		self.web_time_offset.setValue(gui_constants.GLOBAL_EHEN_TIME)
		self.continue_a_metadata_fetcher.setChecked(gui_constants.CONTINUE_AUTO_METADATA_FETCHER)
		self.use_jpn_title.setChecked(gui_constants.USE_JPN_TITLE)

		# Web / Exhentai
		self.ipbid_edit.setText(self.exprops.ipb_id)
		self.ipbpass_edit.setText(self.exprops.ipb_pass)

		# Visual / Grid View / Tooltip
		self.grid_tooltip_group.setChecked(gui_constants.GRID_TOOLTIP)
		self.visual_grid_tooltip_title.setChecked(gui_constants.TOOLTIP_TITLE)
		self.visual_grid_tooltip_author.setChecked(gui_constants.TOOLTIP_AUTHOR)
		self.visual_grid_tooltip_chapters.setChecked(gui_constants.TOOLTIP_CHAPTERS)
		self.visual_grid_tooltip_status.setChecked(gui_constants.TOOLTIP_STATUS)
		self.visual_grid_tooltip_type.setChecked(gui_constants.TOOLTIP_TYPE)
		self.visual_grid_tooltip_lang.setChecked(gui_constants.TOOLTIP_LANG)
		self.visual_grid_tooltip_descr.setChecked(gui_constants.TOOLTIP_DESCR)
		self.visual_grid_tooltip_tags.setChecked(gui_constants.TOOLTIP_TAGS)
		self.visual_grid_tooltip_last_read.setChecked(gui_constants.TOOLTIP_LAST_READ)
		self.visual_grid_tooltip_times_read.setChecked(gui_constants.TOOLTIP_TIMES_READ)
		self.visual_grid_tooltip_pub_date.setChecked(gui_constants.TOOLTIP_PUB_DATE)
		self.visual_grid_tooltip_date_added.setChecked(gui_constants.TOOLTIP_DATE_ADDED)
		# Visual / Grid View / Gallery
		self.external_viewer_ico.setChecked(gui_constants.USE_EXTERNAL_PROG_ICO)
		self.gallery_type_ico.setChecked(gui_constants.DISPLAY_GALLERY_TYPE)
		if gui_constants.GALLERY_FONT_ELIDE:
			self.gallery_text_elide.setChecked(True)
		else:
			self.gallery_text_fit.setChecked(True)
		self.font_lbl.setText(gui_constants.GALLERY_FONT[0])
		self.font_size_lbl.setValue(gui_constants.GALLERY_FONT[1])

		def re_enforce(s):
			if s:
				self.search_on_enter.setChecked(True)
		self.search_allow_regex.clicked.connect(re_enforce)

		if gui_constants.SEARCH_ON_ENTER:
			self.search_on_enter.setChecked(True)
		else:
			self.search_every_keystroke.setChecked(True)
		# Visual / Grid View / Colors
		self.grid_label_color.setText(gui_constants.GRID_VIEW_LABEL_COLOR)
		self.grid_title_color.setText(gui_constants.GRID_VIEW_TITLE_COLOR)
		self.grid_artist_color.setText(gui_constants.GRID_VIEW_ARTIST_COLOR)

		# Advanced / Misc / External Viewer
		self.external_viewer_path.setText(gui_constants.EXTERNAL_VIEWER_PATH)

	def accept(self):
		set = settings.set

		# App / Monitor / misc
		gui_constants.ENABLE_MONITOR = self.enable_monitor.isChecked()
		set(gui_constants.ENABLE_MONITOR, 'Application', 'enable monitor')
		gui_constants.LOOK_NEW_GALLERY_STARTUP = self.look_new_gallery_startup.isChecked()
		set(gui_constants.LOOK_NEW_GALLERY_STARTUP, 'Application', 'look new gallery startup')
		gui_constants.LOOK_NEW_GALLERY_AUTOADD = self.auto_add_new_galleries.isChecked()
		set(gui_constants.LOOK_NEW_GALLERY_AUTOADD, 'Application', 'look new gallery autoadd')
		# App / Monitor / folders
		n = self.folders_layout.rowCount()
		paths = ''
		for x in range(n):
			item = self.folders_layout.takeAt(x+1)
			l_edit = item.widget()
			p = l_edit.text()
			if p:
				if x == n-1:
					paths += '{}'.format(p)
				else:
					paths += '{},'.format(p)
		set(paths, 'Application', 'monitor paths')
		gui_constants.MONITOR_PATHS = paths.split(',')

		# Web / General
		if self.default_ehen_url.isChecked():
			gui_constants.DEFAULT_EHEN_URL = 'http://g.e-hentai.org/'
		else:
			gui_constants.DEFAULT_EHEN_URL = 'http://exhentai.org/'
		set(gui_constants.DEFAULT_EHEN_URL, 'Web', 'default ehen url')

		gui_constants.REPLACE_METADATA = self.replace_metadata.isChecked()
		set(gui_constants.REPLACE_METADATA, 'Web', 'replace metadata')

		gui_constants.ALWAYS_CHOOSE_FIRST_HIT = self.always_first_hit.isChecked()
		set(gui_constants.ALWAYS_CHOOSE_FIRST_HIT, 'Web', 'always choose first hit')

		gui_constants.GLOBAL_EHEN_TIME = self.web_time_offset.value()
		set(gui_constants.GLOBAL_EHEN_TIME, 'Web', 'global ehen time offset')

		gui_constants.CONTINUE_AUTO_METADATA_FETCHER = self.continue_a_metadata_fetcher.isChecked()
		set(gui_constants.CONTINUE_AUTO_METADATA_FETCHER, 'Web', 'continue auto metadata fetcher')

		gui_constants.USE_JPN_TITLE = self.use_jpn_title.isChecked()
		set(gui_constants.USE_JPN_TITLE, 'Web', 'use jpn title')

		# Web / ExHentai
		self.exprops.ipb_id = self.ipbid_edit.text()
		self.exprops.ipb_pass = self.ipbpass_edit.text()

		# Visual / Grid View / Tooltip
		gui_constants.GRID_TOOLTIP = self.grid_tooltip_group.isChecked()
		set(gui_constants.GRID_TOOLTIP, 'Visual', 'grid tooltip')
		gui_constants.TOOLTIP_TITLE = self.visual_grid_tooltip_title.isChecked()
		set(gui_constants.TOOLTIP_TITLE, 'Visual', 'tooltip title')
		gui_constants.TOOLTIP_AUTHOR = self.visual_grid_tooltip_author.isChecked()
		set(gui_constants.TOOLTIP_AUTHOR, 'Visual', 'tooltip author')
		gui_constants.TOOLTIP_CHAPTERS = self.visual_grid_tooltip_chapters.isChecked()
		set(gui_constants.TOOLTIP_CHAPTERS, 'Visual', 'tooltip chapters')
		gui_constants.TOOLTIP_STATUS = self.visual_grid_tooltip_status.isChecked()
		set(gui_constants.TOOLTIP_STATUS, 'Visual', 'tooltip status')
		gui_constants.TOOLTIP_TYPE = self.visual_grid_tooltip_type.isChecked()
		set(gui_constants.TOOLTIP_TYPE, 'Visual', 'tooltip type')
		gui_constants.TOOLTIP_LANG = self.visual_grid_tooltip_lang.isChecked()
		set(gui_constants.TOOLTIP_LANG, 'Visual', 'tooltip lang')
		gui_constants.TOOLTIP_DESCR = self.visual_grid_tooltip_descr.isChecked()
		set(gui_constants.TOOLTIP_DESCR, 'Visual', 'tooltip descr')
		gui_constants.TOOLTIP_TAGS = self.visual_grid_tooltip_tags.isChecked()
		set(gui_constants.TOOLTIP_TAGS, 'Visual', 'tooltip tags')
		gui_constants.TOOLTIP_LAST_READ = self.visual_grid_tooltip_last_read.isChecked()
		set(gui_constants.TOOLTIP_LAST_READ, 'Visual', 'tooltip last read')
		gui_constants.TOOLTIP_TIMES_READ = self.visual_grid_tooltip_times_read.isChecked()
		set(gui_constants.TOOLTIP_TIMES_READ, 'Visual', 'tooltip times read')
		gui_constants.TOOLTIP_PUB_DATE = self.visual_grid_tooltip_pub_date.isChecked()
		set(gui_constants.TOOLTIP_PUB_DATE, 'Visual', 'tooltip pub date')
		gui_constants.TOOLTIP_DATE_ADDED = self.visual_grid_tooltip_date_added.isChecked()
		set(gui_constants.TOOLTIP_DATE_ADDED, 'Visual', 'tooltip date added')
		# Visual / Grid View / Gallery
		gui_constants.USE_EXTERNAL_PROG_ICO = self.external_viewer_ico.isChecked()
		set(gui_constants.USE_EXTERNAL_PROG_ICO, 'Visual', 'use external prog ico')
		gui_constants.DISPLAY_GALLERY_TYPE = self.gallery_type_ico.isChecked()
		set(gui_constants.DISPLAY_GALLERY_TYPE, 'Visual', 'display gallery type')
		if self.gallery_text_elide.isChecked():
			gui_constants.GALLERY_FONT_ELIDE = True
		else:
			gui_constants.GALLERY_FONT_ELIDE = False
		set(gui_constants.GALLERY_FONT_ELIDE, 'Visual', 'gallery font elide')
		gui_constants.GALLERY_FONT = (self.font_lbl.text(), self.font_size_lbl.value())
		set(gui_constants.GALLERY_FONT[0], 'Visual', 'gallery font family')
		set(gui_constants.GALLERY_FONT[1], 'Visual', 'gallery font size')
		# Visual / Grid View / Colors
		if self.color_checker(self.grid_title_color.text()):
			gui_constants.GRID_VIEW_TITLE_COLOR = self.grid_title_color.text()
			set(gui_constants.GRID_VIEW_TITLE_COLOR, 'Visual', 'grid view title color')
		if self.color_checker(self.grid_artist_color.text()):
			gui_constants.GRID_VIEW_ARTIST_COLOR = self.grid_artist_color.text()
			set(gui_constants.GRID_VIEW_ARTIST_COLOR, 'Visual', 'grid view artist color')
		if self.color_checker(self.grid_label_color.text()):
			gui_constants.GRID_VIEW_LABEL_COLOR = self.grid_label_color.text()
			set(gui_constants.GRID_VIEW_LABEL_COLOR, 'Visual', 'grid view label color')

		# Advanced / Misc
		# Advanced / Misc / Grid View
		gui_constants.SCROLL_SPEED = self.scroll_speed
		set(self.scroll_speed, 'Advanced', 'scroll speed')
		self.scroll_speed_changed.emit()
		gui_constants.THUMBNAIL_CACHE_SIZE = self.cache_size
		set(self.cache_size[1], 'Advanced', 'cache size')
		QPixmapCache.setCacheLimit(self.cache_size[0]*
							 self.cache_size[1])
		# Advanced / Misc / Search
		gui_constants.ALLOW_SEARCH_REGEX = self.search_allow_regex.isChecked()
		set(gui_constants.ALLOW_SEARCH_REGEX, 'Advanced', 'allow search regex')
		gui_constants.SEARCH_AUTOCOMPLETE = self.search_autocomplete.isChecked()
		set(gui_constants.SEARCH_AUTOCOMPLETE, 'Advanced', 'search autocomplete')
		if self.search_on_enter.isChecked():
			gui_constants.SEARCH_ON_ENTER = True
		else:
			gui_constants.SEARCH_ON_ENTER = False
		set(gui_constants.SEARCH_ON_ENTER, 'Advanced', 'search on enter')

		# Advanced / Misc / External Viewer
		if not self.external_viewer_path.text():
			gui_constants.USE_EXTERNAL_VIEWER = False
			set(False, 'Advanced', 'use external viewer')
		else:
			gui_constants.USE_EXTERNAL_VIEWER = True
			set(True, 'Advanced', 'use external viewer')
			gui_constants._REFRESH_EXTERNAL_VIEWER = True
		gui_constants.EXTERNAL_VIEWER_PATH = self.external_viewer_path.text()
		set(gui_constants.EXTERNAL_VIEWER_PATH,'Advanced', 'external viewer path')

		settings.save()
		self.close()

	def init_right_panel(self):

		#def title_def(title):
		#	title_lbl = QLabel(title)
		#	f = QFont()
		#	f.setPixelSize(16)
		#	title_lbl.setFont(f)
		#	return title_lbl

		def groupbox(name, layout, parent):
			g = QGroupBox(name, parent)
			l = layout(g)
			return g, l

		def option_lbl_checkbox(text, optiontext, parent=None):
			l = QLabel(text)
			c = QCheckBox(text, parent)
			return l, c

		# App
		application = QTabWidget()
		self.application_index = self.right_panel.addWidget(application)
		application_general = QWidget()
		app_general_m_l = QFormLayout(application_general)
		application.addTab(application_general, 'General')

		# App / General / gallery

		app_gallery_group, app_gallery_l = groupbox('Gallery', QFormLayout, self)
		app_general_m_l.addRow(app_gallery_group)
		self.scroll_to_new_galleries = QCheckBox("Scroll to newly added galleries")
		app_gallery_l.addRow(self.scroll_to_new_galleries)
		self.subfolder_as_chapters = QCheckBox("Treat subfolders as galleries")
		app_gallery_l.addRow(self.subfolder_as_chapters)
		self.rename_g_source_group, rename_g_source_l = groupbox('Rename gallery source',
													  QFormLayout, app_gallery_group)
		self.rename_g_source_group.setCheckable(True)
		app_gallery_l.addRow(self.rename_g_source_group)
		rename_g_source_l.addRow(QLabel("Check what to include when renaming gallery source. (Same order)"))
		rename_g_source_flow_l = FlowLayout()
		rename_g_source_l.addRow(rename_g_source_flow_l)
		self.rename_artist = QCheckBox("Artist")
		self.rename_title = QCheckBox("Title")
		self.rename_lang = QCheckBox("Language")
		self.rename_title.setChecked(True)
		self.rename_title.setDisabled(True)
		rename_g_source_flow_l.addWidget(self.rename_artist)
		rename_g_source_flow_l.addWidget(self.rename_title)
		rename_g_source_flow_l.addWidget(self.rename_lang)
		random_gallery_opener, random_g_opener_l = groupbox('Random Gallery Opener', QFormLayout, app_gallery_group)
		app_gallery_l.addRow(random_gallery_opener)
		self.open_random_g_chapters = QCheckBox("Open random gallery chapters")
		random_g_opener_l.addRow(self.open_random_g_chapters)

		# App / Monitor
		app_monitor_page = QScrollArea()
		app_monitor_page.setBackgroundRole(QPalette.Base)
		app_monitor_dummy = QWidget()
		app_monitor_page.setWidgetResizable(True)
		app_monitor_page.setWidget(app_monitor_dummy)
		application.addTab(app_monitor_page, 'Monitoring')
		app_monitor_m_l = QVBoxLayout(app_monitor_dummy)
		# App / Monitor / misc
		app_monitor_misc_group = QGroupBox('General *', self)
		app_monitor_m_l.addWidget(app_monitor_misc_group)
		app_monitor_misc_m_l = QFormLayout(app_monitor_misc_group)
		monitor_info = QLabel('Directory monitoring will monitor the specified directories for any'+
						' gallery events. For example if you delete a gallery source in one of your'+
						' monitored directories the application will inform you about it, and ask if'+
						' you want to delete the gallery from the application as well.')
		monitor_info.setWordWrap(True)
		app_monitor_misc_m_l.addRow(monitor_info)
		self.enable_monitor = QCheckBox('Enable directory monitoring')
		app_monitor_misc_m_l.addRow(self.enable_monitor)
		self.look_new_gallery_startup = QGroupBox('Scan for new galleries on startup', self)
		app_monitor_misc_m_l.addRow(self.look_new_gallery_startup)
		self.look_new_gallery_startup.setCheckable(True)
		look_new_gallery_startup_m_l = QVBoxLayout(self.look_new_gallery_startup)
		self.auto_add_new_galleries = QCheckBox('Automatically add found galleries')
		look_new_gallery_startup_m_l.addWidget(self.auto_add_new_galleries)

		# App / Monitor / folders
		app_monitor_group = QGroupBox('Directories *', self)
		app_monitor_m_l.addWidget(app_monitor_group, 1)
		app_monitor_folders_m_l = QVBoxLayout(app_monitor_group)
		app_monitor_folders_add = QPushButton('+')
		app_monitor_folders_add.clicked.connect(self.add_folder_monitor)
		app_monitor_folders_add.setMaximumWidth(20)
		app_monitor_folders_add.setMaximumHeight(20)
		app_monitor_folders_m_l.addWidget(app_monitor_folders_add, 0, Qt.AlignRight)
		self.folders_layout = QFormLayout()
		app_monitor_folders_m_l.addLayout(self.folders_layout)

		# Web
		web = QTabWidget()
		self.web_index = self.right_panel.addWidget(web)
		web_general_page = QScrollArea()
		web_general_page.setBackgroundRole(QPalette.Base)
		web_general_page.setWidgetResizable(True)
		web.addTab(web_general_page, 'General')
		web_general_dummy = QWidget()
		web_general_page.setWidget(web_general_dummy)
		web_general_m_l = QVBoxLayout(web_general_dummy)
		metadata_fetcher_group = QGroupBox('Metadata', self)
		web_general_m_l.addWidget(metadata_fetcher_group)
		metadata_fetcher_m_l = QFormLayout(metadata_fetcher_group)
		self.default_ehen_url = QRadioButton('g.e-hentai.org', metadata_fetcher_group)
		self.exhentai_ehen_url = QRadioButton('exhentai.org', metadata_fetcher_group)
		ehen_url_l = QHBoxLayout()
		ehen_url_l.addWidget(self.default_ehen_url)
		ehen_url_l.addWidget(self.exhentai_ehen_url, 1)
		metadata_fetcher_m_l.addRow('Default URL:', ehen_url_l)
		self.continue_a_metadata_fetcher = QCheckBox('Continue from where auto metadata fetcher left off')
		metadata_fetcher_m_l.addRow(self.continue_a_metadata_fetcher)
		self.use_jpn_title = QCheckBox('Use japanese title')
		metadata_fetcher_m_l.addRow(self.use_jpn_title)
		time_offset_info = QLabel('To avoid getting banned, we need to impose a delay between our requests.'+
							' I have made it so you cannot set the delay lower than the recommended (I don\'t'+
							' want you to get banned, anon).\nSpecify the delay between requests in seconds.')
		time_offset_info.setWordWrap(True)
		self.web_time_offset = QSpinBox()
		self.web_time_offset.setMaximumWidth(40)
		self.web_time_offset.setMinimum(4)
		self.web_time_offset.setMaximum(99)
		metadata_fetcher_m_l.addRow(time_offset_info)
		metadata_fetcher_m_l.addRow('Requests delay in', self.web_time_offset)
		replace_metadata_info = QLabel('When fetching for metadata the new metadata will be appended'+
								 ' to the gallery by default. This means that new data will only be set if'+
								 ' the field was empty. There is however a special case for namespace & tags.'+
								 ' We go through all the new namespace & tags to only add those that'+
								 ' do not already exists.\n\nEnabling this option makes it so that a gallery\'s old data'+
								 ' are deleted and replaced with the new data.')
		replace_metadata_info.setWordWrap(True)
		self.replace_metadata = QCheckBox('Replace old metadata with new metadata')
		metadata_fetcher_m_l.addRow(replace_metadata_info)
		metadata_fetcher_m_l.addRow(self.replace_metadata)
		first_hit_info = QLabel('By default, you get to choose which gallery to extract metadata from when'+
						  ' there is more than one gallery found when searching.\n'+
						  'Enabling this option makes it choose the first hit, saving you from moving your mouse.')
		first_hit_info.setWordWrap(True)
		self.always_first_hit = QCheckBox('Always choose first hit')
		metadata_fetcher_m_l.addRow(first_hit_info)
		metadata_fetcher_m_l.addRow(self.always_first_hit)

		# Web / Exhentai
		exhentai_page = QWidget()
		web.addTab(exhentai_page, 'ExHentai')
		ipb_layout = QFormLayout()
		exhentai_page.setLayout(ipb_layout)
		self.ipbid_edit = QLineEdit()
		self.ipbpass_edit = QLineEdit()
		exh_tutorial = QLabel(gui_constants.EXHEN_COOKIE_TUTORIAL)
		exh_tutorial.setTextFormat(Qt.RichText)
		ipb_layout.addRow('IPB Member ID:', self.ipbid_edit)
		ipb_layout.addRow('IPB Pass Hash:', self.ipbpass_edit)
		ipb_layout.addRow(exh_tutorial)

		# Visual
		visual = QTabWidget()
		self.visual_index = self.right_panel.addWidget(visual)
		visual_general_page = QWidget()
		visual.addTab(visual_general_page, 'General')

		grid_view_general_page = QWidget()
		visual.addTab(grid_view_general_page, 'Grid View')
		grid_view_layout = QVBoxLayout()
		grid_view_layout.addWidget(QLabel('Options marked with * requires application restart'),
						   0, Qt.AlignTop)
		grid_view_general_page.setLayout(grid_view_layout)
		# grid view
		# grid view / tooltip
		self.grid_tooltip_group = QGroupBox('Tooltip', grid_view_general_page)
		self.grid_tooltip_group.setCheckable(True)
		grid_view_layout.addWidget(self.grid_tooltip_group, 0, Qt.AlignTop)
		grid_tooltip_layout = QFormLayout()
		self.grid_tooltip_group.setLayout(grid_tooltip_layout)
		grid_tooltip_layout.addRow(QLabel('Control what is'+
									' displayed in the tooltip'))
		grid_tooltips_hlayout = FlowLayout()
		grid_tooltip_layout.addRow(grid_tooltips_hlayout)
		self.visual_grid_tooltip_title = QCheckBox('Title')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_title)
		self.visual_grid_tooltip_author = QCheckBox('Author')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_author)
		self.visual_grid_tooltip_chapters = QCheckBox('Chapters')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_chapters)
		self.visual_grid_tooltip_status = QCheckBox('Status')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_status)
		self.visual_grid_tooltip_type = QCheckBox('Type')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_type)
		self.visual_grid_tooltip_lang = QCheckBox('Language')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_lang)
		self.visual_grid_tooltip_descr = QCheckBox('Description')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_descr)
		self.visual_grid_tooltip_tags = QCheckBox('Tags')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_tags)
		self.visual_grid_tooltip_last_read = QCheckBox('Last read')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_last_read)
		self.visual_grid_tooltip_times_read = QCheckBox('Times read')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_times_read)
		self.visual_grid_tooltip_pub_date = QCheckBox('Publication Date')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_pub_date)
		self.visual_grid_tooltip_date_added = QCheckBox('Date added')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_date_added)
		# grid view / gallery
		grid_gallery_group = QGroupBox('Gallery', grid_view_general_page)
		grid_view_layout.addWidget(grid_gallery_group, 0, Qt.AlignTop)
		grid_gallery_main_l = QFormLayout()
		grid_gallery_main_l.setFormAlignment(Qt.AlignLeft)
		grid_gallery_group.setLayout(grid_gallery_main_l)
		grid_gallery_display = FlowLayout()
		grid_gallery_main_l.addRow('Display on gallery:', grid_gallery_display)
		self.external_viewer_ico = QCheckBox('External Viewer')
		self.external_viewer_ico.setDisabled(True)
		grid_gallery_display.addWidget(self.external_viewer_ico)
		self.gallery_type_ico = QCheckBox('File Type')
		self.gallery_type_ico.setDisabled(True)
		grid_gallery_display.addWidget(self.gallery_type_ico)
		gallery_text_mode = QWidget()
		grid_gallery_main_l.addRow('Text Mode:', gallery_text_mode)
		gallery_text_mode_l = QHBoxLayout()
		gallery_text_mode.setLayout(gallery_text_mode_l)
		self.gallery_text_elide = QRadioButton('Elide text', gallery_text_mode)
		self.gallery_text_fit = QRadioButton('Fit text', gallery_text_mode)
		gallery_text_mode_l.addWidget(self.gallery_text_elide, 0, Qt.AlignLeft)
		gallery_text_mode_l.addWidget(self.gallery_text_fit, 0, Qt.AlignLeft)
		gallery_text_mode_l.addWidget(Spacer('h'), 1, Qt.AlignLeft)
		gallery_font = QHBoxLayout()
		grid_gallery_main_l.addRow('Font:*', gallery_font)
		self.font_lbl = QLabel()
		self.font_size_lbl = QSpinBox()
		self.font_size_lbl.setMaximum(100)
		self.font_size_lbl.setMinimum(1)
		self.font_size_lbl.setToolTip('Font size in pixels')
		choose_font = QPushButton('Choose font')
		choose_font.clicked.connect(self.choose_font)
		gallery_font.addWidget(self.font_lbl, 0, Qt.AlignLeft)
		gallery_font.addWidget(self.font_size_lbl, 0, Qt.AlignLeft)
		gallery_font.addWidget(choose_font, 0, Qt.AlignLeft)
		gallery_font.addWidget(Spacer('h'), 1, Qt.AlignLeft)
		# grid view / colors
		grid_colors_group = QGroupBox('Colors', grid_view_general_page)
		grid_view_layout.addWidget(grid_colors_group, 1, Qt.AlignTop)
		grid_colors_l = QFormLayout()
		grid_colors_group.setLayout(grid_colors_l)
		def color_lineedit():
			l = QLineEdit()
			l.setPlaceholderText('Hex colors. Eg.: #323232')
			l.setMaximumWidth(200)
			return l
		self.grid_label_color = color_lineedit()
		self.grid_title_color = color_lineedit()
		self.grid_artist_color = color_lineedit()
		grid_colors_l.addRow('Label color:', self.grid_label_color)
		grid_colors_l.addRow('Title color:', self.grid_title_color)
		grid_colors_l.addRow('Artist color:', self.grid_artist_color)

		style_page = QWidget()
		visual.addTab(style_page, 'Style')
		visual.setTabEnabled(0, False)
		visual.setTabEnabled(2, False)
		visual.setCurrentIndex(1)

		# Advanced
		advanced = QTabWidget()
		self.advanced_index = self.right_panel.addWidget(advanced)
		advanced_misc = QWidget()
		advanced.addTab(advanced_misc, 'Misc')
		advanced_misc_main_layout = QVBoxLayout()
		advanced_misc.setLayout(advanced_misc_main_layout)
		misc_controls_layout = QFormLayout()
		misc_controls_layout.addWidget(QLabel('Options marked with * requires application restart'))
		advanced_misc_main_layout.addLayout(misc_controls_layout)
		# Advanced / Misc / Grid View
		misc_gridview = QGroupBox('Grid View')
		misc_controls_layout.addWidget(misc_gridview)
		misc_gridview_layout = QFormLayout()
		misc_gridview.setLayout(misc_gridview_layout)
		# Advanced / Misc / Grid View / scroll speed
		scroll_speed_spin_box = QSpinBox()
		scroll_speed_spin_box.setFixedWidth(60)
		scroll_speed_spin_box.setToolTip('Control the speed when scrolling in'+
								   ' grid view. DEFAULT: 7')
		scroll_speed_spin_box.setValue(self.scroll_speed)
		def scroll_speed(v): self.scroll_speed = v
		scroll_speed_spin_box.valueChanged[int].connect(scroll_speed)
		misc_gridview_layout.addRow('Scroll speed:', scroll_speed_spin_box)
		# Advanced / Misc / Grid View / cache size
		cache_size_spin_box = QSpinBox()
		cache_size_spin_box.setFixedWidth(120)
		cache_size_spin_box.setMaximum(999999999)
		cache_size_spin_box.setToolTip('This will greatly improve the grid view.' +
								 ' Increase the value if you experience lag when scrolling'+
								 ' through galleries. DEFAULT: 200 MiB')
		def cache_size(c): self.cache_size = (self.cache_size[0], c)
		cache_size_spin_box.setValue(self.cache_size[1])
		cache_size_spin_box.valueChanged[int].connect(cache_size)
		misc_gridview_layout.addRow('Cache Size (MiB):', cache_size_spin_box)		
		# Advanced / Misc / Regex
		misc_search = QGroupBox('Search')
		misc_controls_layout.addWidget(misc_search)
		misc_search_layout = QFormLayout()
		misc_search.setLayout(misc_search_layout)
		search_allow_regex_l = QHBoxLayout()
		self.search_allow_regex = QCheckBox()
		self.search_allow_regex.setChecked(gui_constants.ALLOW_SEARCH_REGEX)
		self.search_allow_regex.adjustSize()
		self.search_allow_regex.setToolTip('A regex cheatsheet is located at About->Regex Cheatsheet')
		search_allow_regex_l.addWidget(self.search_allow_regex)
		search_allow_regex_l.addWidget(QLabel('A regex cheatsheet is located at About->Regex Cheatsheet'))
		search_allow_regex_l.addWidget(Spacer('h'))
		misc_search_layout.addRow('Regex:', search_allow_regex_l)
		# Advanced / Misc / Regex / autocomplete
		self.search_autocomplete = QCheckBox('*')
		self.search_autocomplete.setChecked(gui_constants.SEARCH_AUTOCOMPLETE)
		self.search_autocomplete.setToolTip('Turn autocomplete on/off')
		misc_search_layout.addRow('Autocomplete', self.search_autocomplete)
		# Advanced / Misc / Regex / search behaviour
		self.search_every_keystroke = QRadioButton('Search on every keystroke *', misc_search)
		misc_search_layout.addRow(self.search_every_keystroke)
		self.search_on_enter = QRadioButton('Search on enter-key *', misc_search)
		misc_search_layout.addRow(self.search_on_enter)
		# Advanced / Misc / External Viewer
		misc_external_viewer = QGroupBox('External Viewer')
		misc_controls_layout.addWidget(misc_external_viewer)
		misc_external_viewer_l = QFormLayout()
		misc_external_viewer.setLayout(misc_external_viewer_l)
		misc_external_viewer_l.addRow(QLabel(gui_constants.SUPPORTED_EXTERNAL_VIEWER_LBL))
		self.external_viewer_path = PathLineEdit(misc_external_viewer, False)
		self.external_viewer_path.setPlaceholderText('Right/Left-click to open folder explorer.'+
							  ' Leave empty to use default viewer')
		self.external_viewer_path.setToolTip('Right/Left-click to open folder explorer.'+
							  ' Leave empty to use default viewer')
		self.external_viewer_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		misc_external_viewer_l.addRow('Path:', self.external_viewer_path)


		# Advanced / Database
		advanced_db_page = QWidget()
		advanced.addTab(advanced_db_page, 'Database')
		advanced.setTabEnabled(1, False)


		# About
		about = QTabWidget()
		self.about_index = self.right_panel.addWidget(about)
		about_happypanda_page = QWidget()
		about_troubleshoot_page = QWidget()
		about.addTab(about_happypanda_page, 'About Happypanda')
		about_layout = QVBoxLayout()
		about_happypanda_page.setLayout(about_layout)
		info_lbl = QLabel('<b>Author:</b> <a href=\'https://github.com/Pewpews\'>'+
					'Pewpews</a><br/>'+
					'Chat: <a href=\'https://gitter.im/Pewpews/happypanda\'>'+
					'Gitter chat</a><br/>'+
					'Email: happypandabugs@gmail.com<br/>'+
					'<b>Current version {}</b><br/>'.format(gui_constants.vs)+
					'Happypanda was created using:<br/>'+
					'- Python 3.4<br/>'+
					'- The Qt5 Framework')
		info_lbl.setOpenExternalLinks(True)
		about_layout.addWidget(info_lbl, 0, Qt.AlignTop)
		gpl_lbl = QLabel(gui_constants.GPL)
		gpl_lbl.setOpenExternalLinks(True)
		gpl_lbl.setWordWrap(True)
		about_layout.addWidget(gpl_lbl, 0, Qt.AlignTop)
		about_layout.addWidget(Spacer('v'))
		# About / Tags
		about_tags_page = QWidget()
		about.addTab(about_tags_page, 'Tags')
		about.setTabEnabled(1, False)
		# list of tags/namespaces here

		# About / Troubleshooting
		about.addTab(about_troubleshoot_page, 'Troubleshooting Guide')
		troubleshoot_layout = QVBoxLayout()
		about_troubleshoot_page.setLayout(troubleshoot_layout)
		guide_lbl = QLabel(gui_constants.TROUBLE_GUIDE)
		guide_lbl.setTextFormat(Qt.RichText)
		guide_lbl.setOpenExternalLinks(True)
		troubleshoot_layout.addWidget(guide_lbl, 0, Qt.AlignTop)
		troubleshoot_layout.addWidget(Spacer('v'))
		# About / Regex Cheatsheet
		about_s_regex = QGroupBox('Regex')
		about.addTab(about_s_regex, 'Regex Cheatsheet')
		about_s_regex_l = QFormLayout()
		about_s_regex.setLayout(about_s_regex_l)
		about_s_regex_l.addRow('\\\\\\\\', QLabel('Match literally \\'))
		about_s_regex_l.addRow('.', QLabel('Match any single character'))
		about_s_regex_l.addRow('^', QLabel('Start of string'))
		about_s_regex_l.addRow('$', QLabel('End of string'))
		about_s_regex_l.addRow('\\d', QLabel('Match any decimal digit'))
		about_s_regex_l.addRow('\\D', QLabel('Match any non-digit character'))
		about_s_regex_l.addRow('\\s', QLabel('Match any whitespace character'))
		about_s_regex_l.addRow('\\S', QLabel('Match any non-whitespace character'))
		about_s_regex_l.addRow('\\w', QLabel('Match any alphanumeric character'))
		about_s_regex_l.addRow('\\W', QLabel('Match any non-alphanumeric character'))
		about_s_regex_l.addRow('*', QLabel('Repeat previous character zero or more times'))
		about_s_regex_l.addRow('+', QLabel('Repeat previous character one or more times'))
		about_s_regex_l.addRow('?', QLabel('Repeat previous character one or zero times'))
		about_s_regex_l.addRow('{m, n}', QLabel('Repeat previous character atleast <i>m</i> times but no more than <i>n</i> times'))
		about_s_regex_l.addRow('(...)', QLabel('Match everything enclosed'))
		about_s_regex_l.addRow('(a|b)', QLabel('Match either a or b'))
		about_s_regex_l.addRow('[abc]', QLabel('Match a single character of: a, b or c'))
		about_s_regex_l.addRow('[^abc]', QLabel('Match a character except: a, b or c'))
		about_s_regex_l.addRow('[a-z]', QLabel('Match a character in the range'))
		about_s_regex_l.addRow('[^a-z]', QLabel('Match a character not in the range'))
		# About / Search tutorial
		about_search_scroll = QScrollArea()
		about_search_scroll.setBackgroundRole(QPalette.Base)
		about_search_scroll.setWidgetResizable(True)
		about_search_tut = QWidget()
		about.addTab(about_search_scroll, 'Search Guide')
		about_search_tut_l = QVBoxLayout()
		about_search_tut.setLayout(about_search_tut_l)
		# General
		about_search_general = QGroupBox('General')
		about_search_tut_l.addWidget(about_search_general)
		about_search_general_l = QFormLayout()
		about_search_general.setLayout(about_search_general_l)
		about_search_general_l.addRow(QLabel(gui_constants.SEARCH_TUTORIAL_GENERAL))
		# Title & Author
		about_search_tit_aut = QGroupBox('Title and Author')
		about_search_tut_l.addWidget(about_search_tit_aut)
		about_search_tit_l = QFormLayout()
		about_search_tit_aut.setLayout(about_search_tit_l)
		about_search_tit_l.addRow(QLabel(gui_constants.SEARCH_TUTORIAL_TIT_AUT))
		# Namespace & Tags
		about_search_tags = QGroupBox('Namespace and Tags')
		about_search_tut_l.addWidget(about_search_tags)
		about_search_tags_l = QFormLayout()
		about_search_tags.setLayout(about_search_tags_l)
		about_search_tags_l.addRow(QLabel(gui_constants.SEARCH_TUTORIAL_TAGS))
		about_search_scroll.setWidget(about_search_tut)

	def add_folder_monitor(self, path=''):
		if not isinstance(path, str):
			path = ''
		l_edit = PathLineEdit()
		l_edit.setText(path)
		n = self.folders_layout.rowCount() + 1
		self.folders_layout.addRow('Dir {}'.format(n), l_edit)

	def color_checker(self, txt):
		allow = False
		if len(txt) == 7:
			if txt[0] == '#':
				allow = True
		return allow

	def choose_font(self):
		tup = QFontDialog.getFont(self)
		font = tup[0]
		if tup[1]:
			self.font_lbl.setText(font.family())
			self.font_size_lbl.setValue(font.pointSize())

	def reject(self):
		self.close()



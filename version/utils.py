#"""
#This file is part of Happypanda.
#Happypanda is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#any later version.
#Happypanda is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU General Public License
#along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
#"""

import datetime
import os
import subprocess
import sys
import logging
import zipfile
import hashlib
import shutil
import uuid
import re
import scandir
import rarfile
import json
import send2trash

from PIL import Image,ImageChops

import app_constants

from database import db_constants

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

IMG_FILES = ('.jpg','.bmp','.png','.gif', '.jpeg')
ARCHIVE_FILES = ('.zip', '.cbz', '.rar', '.cbr')
FILE_FILTER = '*.zip *.cbz *.rar *.cbr'
IMG_FILTER = '*.jpg *.bmp *.png *.jpeg'
rarfile.PATH_SEP = '/'
rarfile.UNRAR_TOOL = app_constants.unrar_tool_path
if not app_constants.unrar_tool_path:
	FILE_FILTER = '*.zip *.cbz'
	ARCHIVE_FILES = ('.zip', '.cbz')

class GMetafile:
	def __init__(self, path=None, archive=''):
		self.metadata = {
			"title":'',
			"artist":'',
			"type":'',
			"tags":{},
			"language":'',
			"pub_date":'',
			"link":'',
			"info":'',

			}
		self.files = []
		if path is None:
			return
		if archive:
			zip = ArchiveFile(archive)
			c = zip.dir_contents(path)
			for x in c:
				if x.endswith(app_constants.GALLERY_METAFILE_KEYWORDS):
					self.files.append(open(zip.extract(x), encoding='utf-8'))
		else:
			for p in scandir.scandir(path):
				if p.name in app_constants.GALLERY_METAFILE_KEYWORDS:
					self.files.append(open(p.path, encoding='utf-8'))
		if self.files:
			self.detect()
		else:
			log_d('No metafile found...')

	def _eze(self, fp):
		if not fp.name.endswith('.json'):
			return
		j = json.load(fp, encoding='utf-8')
		eze = ['gallery_info', 'image_api_key', 'image_info']
		# eze
		if all(x in j for x in eze):
			log_i('Detected metafile: eze')
			ezedata = j['gallery_info']
			t_parser = title_parser(ezedata['title'])
			self.metadata['title'] = t_parser['title']
			self.metadata['type'] = ezedata['category']
			for ns in ezedata['tags']:
				self.metadata['tags'][ns.capitalize()] = ezedata['tags'][ns]
			self.metadata['tags']['default'] = self.metadata['tags'].pop('Misc', [])
			self.metadata['artist'] = self.metadata['tags']['Artist'][0].capitalize()\
				if 'Artist' in self.metadata['tags'] else t_parser['artist']
			self.metadata['language'] = ezedata['language']
			d = ezedata['upload_date']
			# should be zero padded
			d[1] = int("0" + str(d[1])) if len(str(d[1])) == 1 else d[1]
			d[3] = int("0" + str(d[1])) if len(str(d[1])) == 1 else d[1] 
			self.metadata['pub_date'] = datetime.datetime.strptime("{} {} {}".format(d[0], d[1], d[3]), "%Y %m %d")
			l = ezedata['source']
			self.metadata['link'] = 'http://' + l['site'] + '.org/g/' + str(l['gid']) + '/' + l['token']
			return True

	def _hdoujindler(self, fp):
		"HDoujin Downloader"
		if not fp.name.endswith('info.txt'):
			return
		lines = fp.readlines()
		if lines:
			for line in lines:
				splitted = line.split(':')
				if len(splitted) > 1:
					other = splitted[1].strip()
					if not other:
						continue
					l = splitted[0].lower()
					if "title" == l:
						self.metadata['title'] = other
					if "artist" == l:
						self.metadata['artist'] = other.capitalize()
					if "tags" == l:
						self.metadata['tags'].update(tag_to_dict(other))
					if "description" == l:
						self.metadata['info'] = other
					if "circle" in l:
						if not "group" in self.metadata['tags']:
							self.metadata['tags']['group'] = []
							self.metadata['tags']['group'].append(other.strip().lower())

			return True

	def detect(self):
		for fp in self.files:
			with fp:
				z = False
				for x in [self._eze, self._hdoujindler]:
					if x(fp):
						z = True
						break
				if not z:
					log_i('Incompatible metafiles found')

	def update(self, other):
		self.metadata.update((x, y) for x, y in other.metadata.items() if y)

	def apply_gallery(self, gallery):
		log_i('Applying metafile to gallery')
		if self.metadata['title']:
			gallery.title = self.metadata['title']
		if self.metadata['artist']:
			gallery.artist = self.metadata['artist']
		if self.metadata['type']:
			gallery.type = self.metadata['type']
		if self.metadata['tags']:
			gallery.tags = self.metadata['tags']
		if self.metadata['language']:
			gallery.language = self.metadata['language']
		if self.metadata['pub_date']:
			gallery.pub_date = self.metadata['pub_date']
		if self.metadata['link']:
			gallery.link = self.metadata['link']
		if self.metadata['info']:
			gallery.info = self.metadata['info']
		return gallery

def backup_database(db_path=db_constants.DB_PATH):
	log_i("Perfoming database backup")
	date = "{}".format(datetime.datetime.today()).split(' ')[0]
	base_path, name = os.path.split(db_path)
	db_name = "{}-{}".format(date, name)

	current_try = 0
	while current_try < 50:
		if current_try:
			db_name = "{}({})-{}".format(date, current_try, db_name)
		try:
			dst_path = os.path.join(base_path, db_name)
			if os.path.exists(dst_path):
				raise ValueError
			shutil.copyfile(db_path, dst_path)
			break
		except:
			current_try += 1
	log_i("Database backup perfomed: {}".format(db_name))
	return True

def get_date_age(date):
	"""
	Take a datetime and return its "age" as a string.
	The age can be in second, minute, hour, day, month or year. Only the
	biggest unit is considered, e.g. if it's 2 days and 3 hours, "2 days" will
	be returned.
	Make sure date is not in the future, or else it won't work.
	"""

	def formatn(n, s):
		'''Add "s" if it's plural'''

		if n == 1:
			return "1 %s" % s
		elif n > 1:
			return "%d %ss" % (n, s)

	def q_n_r(a, b):
		'''Return quotient and remaining'''

		return a / b, a % b

	class PrettyDelta:
		def __init__(self, dt):
			now = datetime.datetime.now()

			delta = now - dt
			self.day = delta.days
			self.second = delta.seconds

			self.year, self.day = q_n_r(self.day, 365)
			self.month, self.day = q_n_r(self.day, 30)
			self.hour, self.second = q_n_r(self.second, 3600)
			self.minute, self.second = q_n_r(self.second, 60)

		def format(self):
			for period in ['year', 'month', 'day', 'hour', 'minute', 'second']:
				n = getattr(self, period)
				if n > 0.9:
					return formatn(n, period)
			return "0 second"

	return PrettyDelta(date).format()

def all_opposite(*args):
	"Returns true if all items in iterable evaluae to false"
	for iterable in args:
		for x in iterable:
			if x:
				return False
	return True

def update_gallery_path(new_path, gallery):
	"Updates a gallery's chapters path"
	for chap in gallery.chapters:
		head, tail = os.path.split(chap.path)
		if gallery.path == chap.path:
			chap.path = new_path
		elif gallery.path == head:
			chap.path = os.path.join(new_path, tail)

	gallery.path = new_path
	return gallery

def move_files(path, dest=''):
	"""
	Move files to a new destination. If dest is not set,
	imported_galleries_def_path will be used instead.
	"""
	if not dest:
		dest = app_constants.IMPORTED_GALLERY_DEF_PATH
		if not dest:
			return path
	f = os.path.split(path)[1]
	new_path = os.path.join(dest, f)
	if new_path == os.path.join(*os.path.split(path)): # need to unpack to make sure we get the corrct sep
		return path
	if not os.path.exists(new_path):
		new_path = shutil.move(path, new_path)
	else:
		return path
	return new_path

def check_ignore_list(key):
	k = os.path.normcase(key)
	for path in app_constants.IGNORE_PATHS:
		p = os.path.normcase(path)
		if p in k:
			return False
	return True

def gallery_text_fixer(gallery):
	regex_str = app_constants.GALLERY_DATA_FIX_REGEX
	if regex_str:
		try:
			valid_regex = re.compile(regex_str)
		except re.error:
			return None
		if not valid_regex:
			return None

		def replace_regex(text):
			new_text = re.sub(regex_str, app_constants.GALLERY_DATA_FIX_REPLACE, text)
			return new_text

		if app_constants.GALLERY_DATA_FIX_TITLE:
			gallery.title = replace_regex(gallery.title)
		if app_constants.GALLERY_DATA_FIX_ARTIST:
			gallery.artist = replace_regex(gallery.artist)

		return gallery

def b_search(data, key):
	lo = 0
	hi = len(data) - 1
	while hi >= lo:
		mid = lo + (hi - lo) // 2
		if data[mid] < key:
			lo = mid + 1
		elif data[mid] > key:
			hi = mid - 1
		else:
			return data[mid]
	return None

def generate_img_hash(src):
	"""
	Generates sha1 hash based on the given bytes.
	Returns hex-digits
	"""
	chunk = 8129
	sha1 = hashlib.sha1()
	buffer = src.read(chunk)
	log_d("Generating hash")
	while len(buffer) > 0:
		sha1.update(buffer)
		buffer = src.read(chunk)
	return sha1.hexdigest()

class ArchiveFile():
	"""
	Work with archive files, raises exception if instance fails.
	namelist -> returns a list with all files in archive
	extract <- Extracts one specific file to given path
	open -> open the given file in archive, returns bytes
	close -> close archive
	"""
	zip, rar = range(2)
	def __init__(self, filepath):
		self.type = 0
		try:
			if filepath.endswith(ARCHIVE_FILES):
				if filepath.endswith(ARCHIVE_FILES[:2]):
					self.archive = zipfile.ZipFile(os.path.normcase(filepath))
					b_f = self.archive.testzip()
					self.type = self.zip
				elif filepath.endswith(ARCHIVE_FILES[2:]):
					self.archive = rarfile.RarFile(os.path.normcase(filepath))
					b_f = self.archive.testrar()
					self.type = self.rar

				# test for corruption
				if b_f:
					log_w('Bad file found in archive {}'.format(filepath.encode(errors='ignore')))
					raise app_constants.CreateArchiveFail
			else:
				log_e('Archive: Unsupported file format')
				raise app_constants.CreateArchiveFail
		except:
			log.exception('Create archive: FAIL')
			raise app_constants.CreateArchiveFail

	def namelist(self):
		filelist = self.archive.namelist()
		return filelist

	def is_dir(self, name):
		"""
		Checks if the provided name in the archive is a directory or not
		"""
		if not name:
			return False
		if not name in self.namelist():
			log_e('File {} not found in archive'.format(name))
			raise app_constants.FileNotFoundInArchive
		if self.type == self.zip:
			if name.endswith('/'):
				return True
		elif self.type == self.rar:
			info = self.archive.getinfo(name)
			return info.isdir()
		return False

	def dir_list(self, only_top_level=False):
		"""
		Returns a list of all directories found recursively. For directories not in toplevel
		a path in the archive to the diretory will be returned.
		"""
		
		if only_top_level:
			if self.type == self.zip:
				return [x for x in self.namelist() if x.endswith('/') and x.count('/') == 1]
			elif self.type == self.rar:
				potential_dirs = [x for x in self.namelist() if x.count('/') == 0]
				return [x.filename for x in [self.archive.getinfo(y) for y in potential_dirs] if x.isdir()]
		else:
			if self.type == self.zip:
				return [x for x in self.namelist() if x.endswith('/') and x.count('/') >= 1]
			elif self.type == self.rar:
				return [x.filename for x in self.archive.infolist() if x.isdir()]

	def dir_contents(self, dir_name):
		"""
		Returns a list of contents in the directory
		An empty string will return the contents of the top folder
		"""
		if dir_name and not dir_name in self.namelist():
			log_e('Directory {} not found in archive'.format(dir_name))
			raise app_constants.FileNotFoundInArchive
		if not dir_name:
			if self.type == self.zip:
				con = [x for x in self.namelist() if x.count('/') == 0 or \
					(x.count('/') == 1 and x.endswith('/'))]
			elif self.type == self.rar:
				con = [x for x in self.namelist() if x.count('/') == 0]
			return con
		if self.type == self.zip:
			dir_con_start = [x for x in self.namelist() if x.startswith(dir_name)]
			return [x for x in dir_con_start if x.count('/') == dir_name.count('/') or \
				(x.count('/') == 1 + dir_name.count('/') and x.endswith('/'))]
		elif self.type == self.rar:
			return [x for x in self.namelist() if x.startswith(dir_name) and \
				x.count('/') == 1 + dir_name.count('/')]
		return []

	def extract(self, file_to_ext, path=None):
		"""
		Extracts one file from archive to given path
		Creates a temp_dir if path is not specified
		Returns path to the extracted file
		"""
		if not path:
			path = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
			os.mkdir(path)

		if not file_to_ext:
			return self.extract_all(path)
		else:
			if self.type == self.zip:
				membs = []
				for name in self.namelist():
					if name.startswith(file_to_ext) and name != file_to_ext:
						membs.append(name)
				temp_p = self.archive.extract(file_to_ext, path)
				for m in membs:
					self.archive.extract(m, path)
			elif self.type == self.rar:
				temp_p = os.path.join(path, file_to_ext)
				self.archive.extract(file_to_ext, path)
			return temp_p

	def extract_all(self, path=None, member=None):
		"""
		Extracts all files to given path, and returns path
		If path is not specified, a temp dir will be created
		"""
		if not path:
			path = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
			os.mkdir(path)
		if member:
			self.archive.extractall(path, member)
		self.archive.extractall(path)
		return path

	def open(self, file_to_open, fp=False):
		"""
		Returns bytes. If fp set to true, returns file-like object.
		"""
		if fp:
			return self.archive.open(file_to_open)
		else:
			return self.archive.open(file_to_open).read()

	def close(self):
		self.archive.close()

def check_archive(archive_path):
	"""
	Checks archive path for potential galleries.
	Returns a list with a path in archive to galleries
	if there is no directories
	"""
	try:
		zip = ArchiveFile(archive_path)
	except app_constants.CreateArchiveFail:
		return []
	if not zip:
		return []
	galleries = []
	zip_dirs = zip.dir_list()
	def gallery_eval(d):
		con = zip.dir_contents(d)
		if con:
			gallery_probability = len(con)
			for n in con:
				if not n.lower().endswith(IMG_FILES):
					gallery_probability -= 1
			if gallery_probability >= (len(con) * 0.8):
				return d
	if zip_dirs: # There are directories in the top folder
		# check parent
		r = gallery_eval('')
		if r:
			galleries.append('')
		for d in zip_dirs:
			r = gallery_eval(d)
			if r:
				galleries.append(r)
		zip.close()
	else: # all pages are in top folder
		if isinstance(gallery_eval(''), str):
			galleries.append('')
		zip.close()

	return galleries

def recursive_gallery_check(path):
	"""
	Recursively checks a folder for any potential galleries
	Returns a list of paths for directories and a list of tuples where first
	index is path to gallery in archive and second index is path to archive.
	Like this:
	["C:path/to/g"] and [("path/to/g/in/a", "C:path/to/a")]
	"""
	gallery_dirs = []
	gallery_arch = []
	found_paths = 0
	for root, subfolders, files in scandir.walk(path):
		if files:
			for f in files:
				if f.endswith(ARCHIVE_FILES):
					arch_path = os.path.join(root, f)
					for g in check_archive(arch_path):
						found_paths += 1
						gallery_arch.append((g, arch_path))
									
			if not subfolders:
				if not files:
					continue
				gallery_probability = len(files)
				for f in files:
					if not f.lower().endswith(IMG_FILES):
						gallery_probability -= 1
				if gallery_probability >= (len(files) * 0.8):
					found_paths += 1
					gallery_dirs.append(root)
	log_i('Found {} in {}'.format(found_paths, path).encode(errors='ignore'))
	return gallery_dirs, gallery_arch

def today():
	"Returns current date in a list: [dd, Mmm, yyyy]"
	_date = datetime.date.today()
	day = _date.strftime("%d")
	month = _date.strftime("%b")
	year = _date.strftime("%Y")
	return [day, month, year]

def external_viewer_checker(path):
	check_dict = app_constants.EXTERNAL_VIEWER_SUPPORT
	viewer = os.path.split(path)[1]
	for x in check_dict:
		allow = False
		for n in check_dict[x]:
			if viewer.lower() in n.lower():
				allow = True
				break
		if allow:
			return x

def open_chapter(chapterpath, archive=None):
	is_archive = True if archive else False
	if not is_archive:
		chapterpath = os.path.normpath(chapterpath)
	temp_p = archive if is_archive else chapterpath

	def find_f_img_folder():
		filepath = os.path.join(temp_p, [x for x in sorted([y.name for y in scandir.scandir(temp_p)])\
			if x.lower().endswith(IMG_FILES)][0]) # Find first page
		return temp_p if app_constants.USE_EXTERNAL_VIEWER else filepath

	def find_f_img_archive(extract=True):
		zip = ArchiveFile(temp_p)
		if extract:
			app_constants.NOTIF_BAR.add_text('Extracting...')
			t_p = os.path.join('temp', str(uuid.uuid4()))
			os.mkdir(t_p)
			if is_archive or chapterpath.endswith(ARCHIVE_FILES):
				if os.path.isdir(chapterpath):
					t_p = chapterpath
				elif chapterpath.endswith(ARCHIVE_FILES):
					zip2 = ArchiveFile(chapterpath)
					f_d = sorted(zip2.dir_list(True))
					if f_d:
						f_d = f_d[0]
						t_p = zip2.extract(f_d, t_p)
					else:
						t_p = zip2.extract('', t_p)
				else:
					t_p = zip.extract(chapterpath, t_p)
			else:
				zip.extract_all(t_p) # Compatibility reasons..  TODO: REMOVE IN BETA
			if app_constants.USE_EXTERNAL_VIEWER:
				filepath = t_p
			else:
				filepath = os.path.join(t_p, [x for x in sorted([y.name for y in scandir.scandir(t_p)])\
					if x.lower().endswith(IMG_FILES)][0]) # Find first page
				filepath = os.path.abspath(filepath)
		else:
			if is_archive or chapterpath.endswith(ARCHIVE_FILES):
				con = zip.dir_contents('')
				f_img = [x for x in sorted(con) if x.lower().endswith(IMG_FILES)]
				if not f_img:
					log_w('Extracting archive.. There are no images in the top-folder. ({})'.format(archive))
					return find_f_img_archive()
				filepath = os.path.normpath(archive)
			else:
				app_constants.NOTIF_BAR.add_text("Fatal error: Unsupported gallery!")
				raise ValueError("Unsupported gallery version")
		return filepath

	try:
		try: # folder
			filepath = find_f_img_folder()
		except NotADirectoryError: # archive
			try:
				if not app_constants.EXTRACT_CHAPTER_BEFORE_OPENING and app_constants.EXTERNAL_VIEWER_PATH:
					filepath = find_f_img_archive(False)
				else:
					filepath = find_f_img_archive()
			except app_constants.CreateArchiveFail:
				log.exception('Could not open chapter')
				app_constants.NOTIF_BAR.add_text('Could not open chapter. Check happypanda.log for more details.')
				return
	except FileNotFoundError:
		log.exception('Could not find chapter {}'.format(chapterpath))
		app_constants.NOTIF_BAR.add_text("Chapter does no longer exist!")
		return

	try:
		app_constants.NOTIF_BAR.add_text('Opening chapter...')
		if not app_constants.USE_EXTERNAL_VIEWER:
			if sys.platform.startswith('darwin'):
				subprocess.call(('open', filepath))
			elif os.name == 'nt':
				os.startfile(filepath)
			elif os.name == 'posix':
				subprocess.call(('xdg-open', filepath))
		else:
			ext_path = app_constants.EXTERNAL_VIEWER_PATH
			viewer = external_viewer_checker(ext_path)
			if viewer == 'honeyview':
				if app_constants.OPEN_GALLERIES_SEQUENTIALLY:
					subprocess.call((ext_path, filepath))
				else:
					subprocess.Popen((ext_path, filepath))
			else:
				if app_constants.OPEN_GALLERIES_SEQUENTIALLY:
					subprocess.check_call((ext_path, filepath))
				else:
					subprocess.Popen((ext_path, filepath))
	except subprocess.CalledProcessError:
		app_constants.NOTIF_BAR.add_text("Could not open chapter. Invalid external viewer.")
		log.exception('Could not open chapter. Invalid external viewer.')
	except:
		app_constants.NOTIF_BAR.add_text("Could not open chapter for unknown reasons. Check happypanda.log!")
		log_e('Could not open chapter {}'.format(os.path.split(chapterpath)[1]))

def get_gallery_img(path, archive=None):
	"""
	Returns a path to a gallery's cover
	Looks in archive if archive is set.
	"""
	# TODO: add chapter support
	try:
		name = os.path.split(path)[1]
	except IndexError:
		name = os.path.split(path)[0]
	is_archive = True if archive or name.endswith(ARCHIVE_FILES) else False
	real_path = archive if archive else path
	img_path = None
	if is_archive:
		try:
			log_i('Getting image from archive')
			zip = ArchiveFile(real_path)
			temp_path = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
			os.mkdir(temp_path)
			if not archive:
				f_img_name = sorted([img for img in zip.namelist() if img.lower().endswith(IMG_FILES)])[0]
			else:
				f_img_name = sorted([img for img in zip.dir_contents(path) if img.lower().endswith(IMG_FILES)])[0]
			img_path = zip.extract(f_img_name, temp_path)
			zip.close()
		except app_constants.CreateArchiveFail:
			img_path = app_constants.NO_IMAGE_PATH
	elif os.path.isdir(real_path):
		log_i('Getting image from folder')
		first_img = sorted([img.name for img in scandir.scandir(real_path) if img.name.lower().endswith(tuple(IMG_FILES))])
		if first_img:
			img_path = os.path.join(real_path, first_img[0])

	if img_path:
		return os.path.abspath(img_path)
	else:
		log_e("Could not get gallery image")

def tag_to_string(gallery_tag, simple=False):
	"""
	Takes gallery tags and converts it to string, returns string
	if simple is set to True, returns a CSV string, else a dict-like string
	"""
	assert isinstance(gallery_tag, dict), "Please provide a dict like this: {'namespace':['tag1']}"
	string = ""
	if not simple:
		for n, namespace in enumerate(sorted(gallery_tag), 1):
			if len(gallery_tag[namespace]) != 0:
				if namespace != 'default':
					string += namespace + ":"

				# find tags
				if namespace != 'default' and len(gallery_tag[namespace]) > 1:
					string += '['
				for x, tag in enumerate(sorted(gallery_tag[namespace]), 1):
					# if we are at the end of the list
					if x == len(gallery_tag[namespace]):
						string += tag
					else:
						string += tag + ', '
				if namespace != 'default' and len(gallery_tag[namespace]) > 1:
					string += ']'

				# if we aren't at the end of the list
				if not n == len(gallery_tag):
					string += ', '
	else:
		for n, namespace in enumerate(sorted(gallery_tag), 1):
			if len(gallery_tag[namespace]) != 0:
				if namespace != 'default':
					string += namespace + ","

				# find tags
				for x, tag in enumerate(sorted(gallery_tag[namespace]), 1):
					# if we are at the end of the list
					if x == len(gallery_tag[namespace]):
						string += tag
					else:
						string += tag + ', '

				# if we aren't at the end of the list
				if not n == len(gallery_tag):
					string += ', '

	return string

def tag_to_dict(string, ns_capitalize=True):
	"Receives a string of tags and converts it to a dict of tags"
	namespace_tags = {'default':[]}
	level = 0 # so we know if we are in a list
	buffer = ""
	stripped_set = set() # we only need unique values
	for n, x in enumerate(string, 1):

		if x == '[':
			level += 1 # we are now entering a list
		if x == ']':
			level -= 1 # we are now exiting a list


		if x == ',': # if we meet a comma
			# we trim our buffer if we are at top level
			if level is 0:
				# add to list
				stripped_set.add(buffer.strip())
				buffer = ""
			else:
				buffer += x
		elif n == len(string): # or at end of string
			buffer += x
			# add to list
			stripped_set.add(buffer.strip())
			buffer = ""
		else:
			buffer += x

	def tags_in_list(br_tags):
		"Receives a string of tags enclosed in brackets, returns a list with tags"
		unique_tags = set()
		tags = br_tags.replace('[', '').replace(']','')
		tags = tags.split(',')
		for t in tags:
			if len(t) != 0:
				unique_tags.add(t.strip().lower())
		return list(unique_tags)

	unique_tags = set()
	for ns_tag in stripped_set:
		splitted_tag = ns_tag.split(':')
		# if there is a namespace
		if len(splitted_tag) > 1 and len(splitted_tag[0]) != 0:
			if splitted_tag[0] != 'default':
				if ns_capitalize:
					namespace = splitted_tag[0].capitalize()
				else:
					namespace = splitted_tag[0]
			else:
				namespace = splitted_tag[0]
			tags = splitted_tag[1]
			# if tags are enclosed in brackets
			if '[' in tags and ']' in tags:
				tags = tags_in_list(tags)
				tags = [x for x in tags if len(x) != 0]
				# if namespace is already in our list
				if namespace in namespace_tags:
					for t in tags:
						# if tag not already in ns list
						if not t in namespace_tags[namespace]:
							namespace_tags[namespace].append(t)
				else:
					# to avoid empty strings
					namespace_tags[namespace] = tags
			else: # only one tag
				if len(tags) != 0:
					if namespace in namespace_tags:
						namespace_tags[namespace].append(tags)
					else:
						namespace_tags[namespace] = [tags]
		else: # no namespace specified
			tag = splitted_tag[0]
			if len(tag) != 0:
				unique_tags.add(tag.lower())

	if len(unique_tags) != 0:
		for t in unique_tags:
			namespace_tags['default'].append(t)

	return namespace_tags

import re as regex
def title_parser(title):
	"Receives a title to parse. Returns dict with 'title', 'artist' and language"
	" ".join(title.split())
	if '/' in title:
		try:
			title = os.path.split(title)[1]
			if not title:
				title = title
		except IndexError:
			pass

	for x in ARCHIVE_FILES:
		if title.endswith(x):
			title = title[:-len(x)]

	parsed_title = {'title':"", 'artist':"", 'language':""}
	try:
		a = regex.findall('((?<=\[) *[^\]]+( +\S+)* *(?=\]))', title)
		assert len(a) != 0
		artist = a[0][0].strip()
		parsed_title['artist'] = artist

		try:
			assert a[1]
			lang = app_constants.G_LANGUAGES + app_constants.G_CUSTOM_LANGUAGES
			for x in a:
				l = x[0].strip()
				l = l.lower()
				l = l.capitalize()
				if l in lang:
					parsed_title['language'] = l
					break
			else:
				parsed_title['language'] = app_constants.G_DEF_LANGUAGE

		except IndexError:
			pass

		t = title
		for x in a:
			t = t.replace(x[0], '')

		t = t.replace('[]', '')
		final_title = t.strip()
		parsed_title['title'] = final_title
	except AssertionError:
		parsed_title['title'] = title

	return parsed_title

import webbrowser
def open_web_link(url):
	if not url:
		return
	try:
		webbrowser.open_new_tab(url)
	except:
		log_e('Could not open URL in browser')

def open_path(path, select=''):
	""
	try:
		if sys.platform.startswith('darwin'):
			subprocess.Popen(['open', path])
		elif os.name == 'nt':
			if select:
				subprocess.Popen(r'explorer.exe /select,"{}"'.format(os.path.normcase(select)), shell=True)
			else:
				os.startfile(path)
		elif os.name == 'posix':
			subprocess.Popen(('xdg-open', path))
		else:
			app_constants.NOTIF_BAR.add_text("I don't know how you've managed to do this.. If you see this, you're in deep trouble...")
			log_e('Could not open path: no OS found')
	except:
		app_constants.NOTIF_BAR.add_text("Could not open specified location. It might not exist anymore.")
		log_e('Could not open path')

def open_torrent(path):
	if not app_constants.TORRENT_CLIENT:
		open_path(path)
	else:
		subprocess.Popen([app_constants.TORRENT_CLIENT, path])

def delete_path(path):
	"Deletes the provided recursively"
	s = True
	if os.path.exists(path):
		error = ''
		if app_constants.SEND_FILES_TO_TRASH:
			try:
				send2trash.send2trash(path)
			except:
				log.exception("Unable to send file to trash")
				error = 'Unable to send file to trash'
		else:
			try:
				if os.path.isfile(path):
					os.remove(path)
				else:
					shutil.rmtree(path)
			except PermissionError:
				error = 'PermissionError'
			except FileNotFoundError:
				pass

		if error:
			p = os.path.split(path)[1]
			log_e('Failed to delete: {}:{}'.format(error, p))
			app_constants.NOTIF_BAR.add_text('An error occured while trying to delete: {}'.format(error))
			s = False
	return s

def regex_search(a, b, override_case=False):
	"Looks for a in b"
	if a and b:
		try:
			if not app_constants.GALLERY_SEARCH_CASE or override_case:
				if regex.search(a, b, regex.IGNORECASE):
					return True
			else:
				if regex.search(a, b):
					return True
		except regex.error:
			pass
	return False

def search_term(a, b, override_case=False):
	"Searches for a in b"
	if a and b:
		if not app_constants.GALLERY_SEARCH_CASE or override_case:
			b = b.lower()
			a = a.lower()

		if app_constants.GALLERY_SEARCH_STRICT:
			if a == b:
				return True
		else:
			if a in b:
				return True
	return False

def get_terms(term):
	"Dividies term into pieces. Returns a list with the pieces"

	# some variables we will use
	pieces = []
	piece = ''
	qoute_level = 0
	bracket_level = 0
	brackets_tags = {}
	current_bracket_ns = ''
	end_of_bracket = False
	blacklist = ['[', ']', '"', ',']

	for n, x in enumerate(term):
		# if we meet brackets
		if x == '[':
			bracket_level += 1
			brackets_tags[piece] = set() # we want unique tags!
			current_bracket_ns = piece
		elif x == ']':
			bracket_level -= 1
			end_of_bracket = True

		# if we meet a double qoute
		if x == '"':
			if qoute_level > 0:
				qoute_level -= 1
			else:
				qoute_level += 1

		# if we meet a whitespace, comma or end of term and are not in a double qoute
		if (x == ' ' or x == ',' or n == len(term) - 1) and qoute_level == 0:
			# if end of term and x is allowed
			if (n == len(term) - 1) and not x in blacklist and x != ' ':
				piece += x
			if piece:
				if bracket_level > 0 or end_of_bracket: # if we are inside a bracket we put piece in the set
					end_of_bracket = False
					if piece.startswith(current_bracket_ns):
						piece = piece[len(current_bracket_ns):]
					if piece:
						try:
							brackets_tags[current_bracket_ns].add(piece)
						except KeyError: # keyerror when there is a closing bracket without a starting bracket
							pass
				else:
					pieces.append(piece) # else put it in the normal list
			piece = ''
			continue

		# else append to the buffers
		if not x in blacklist:
			if qoute_level > 0: # we want to include everything if in double qoute
				piece += x
			elif x != ' ':
				piece += x

	# now for the bracket tags
	for ns in brackets_tags:
		for tag in brackets_tags[ns]:
			ns_tag = ns
			# if they want to exlucde this tag
			if tag[0] == '-':
				if ns_tag[0] != '-':
					ns_tag = '-' + ns
				tag = tag[1:] # remove the '-'

			# put them together
			ns_tag += tag

			# done
			pieces.append(ns_tag)

	return pieces

def image_greyscale(filepath):
	"""
	Check if image is monochrome (1 channel or 3 identical channels)
	"""
	im = Image.open(filepath).convert("RGB")
	if im.mode not in ("L", "RGB"):
		return False

	if im.mode == "RGB":
		rgb = im.split()
		if ImageChops.difference(rgb[0],rgb[1]).getextrema()[1] != 0: 
			return False
		if ImageChops.difference(rgb[0],rgb[2]).getextrema()[1] != 0: 
			return False
	return True



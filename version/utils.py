"""
This file is part of Happypanda.
Happypanda is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
any later version.
Happypanda is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
"""

import time, datetime, os, subprocess, sys, logging, zipfile
import hashlib, shutil

from .gui import gui_constants

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

IMG_FILES =  ['jpg','bmp','png','gif']
ARCHIVE_FILES = ['.zip', '.cbz']

def generate_img_hash(src):
	"""
	Generates sha1 hash based on the given bytes.
	Returns hex-digits
	"""
	chunk = 8129
	sha1 = hashlib.sha1()
	buffer = src.read(chunk)
	while len(buffer) > 0:
		sha1.update(buffer)
		buffer = src.read(chunk)
	return sha1.hexdigest()

class CreateZipFail(Exception): pass

class ArchiveFile():
	"""
	Work with zip files, raises exception if instance fails.
	namelist -> returns a list with all files in archive
	extract <- Extracts one specific file to given path
	open -> open the given file in archive, returns bytes
	close -> close archive
	# Most of the code are from kunesj on GitHub #
	"""
	def __init__(self, filepath):
		extension = filepath[-4:]

		if extension in ARCHIVE_FILES:
			try:
				self.archive = zipfile.ZipFile(filepath)
			except:
				log_e('Create ZIP: FAIL')
				raise CreateZipFail
		else:
			log_e('Archive: Unsupported file format')
			raise Exception

	def namelist(self):
		filelist = self.archive.namelist()
		return filelist

	def extract(self, file_to_ext, path):
		"""
		Extracts one file from archive to given path
		Returns path to the extracted file
		"""

		return self.archive.extract(file_to_ext, path)

	def extract_all(self, path):
		"""
		Extracts all files to given path
		"""
		# TODO: Check contents of archive before extracting
		self.archive.extractall(path)

	def open(self, file_to_open):
		return self.archive.open(file_to_open).read()

	def close(self):
		self.archive.close()

def today():
	"Returns current date in a list: [dd, Mmm, yyyy]"
	_date = datetime.date.today()
	day = _date.strftime("%d")
	month = _date.strftime("%b")
	year = _date.strftime("%Y")
	return [day, month, year]

def external_viewer_checker(path):
	check_dict = gui_constants.EXTERNAL_VIEWER_SUPPORT
	viewer = os.path.split(path)[1]
	for x in check_dict:
		allow = False
		for n in check_dict[x]:
			if viewer.lower() in n.lower():
				allow = True
				break
		if allow:
			return x

def open_chapter(chapterpath):
	try:
		try: # folder
			filepath = os.path.join(chapterpath, [x for x in sorted(os.listdir(chapterpath))\
				if x[-3:] in IMG_FILES][0]) # Find first page
		except NotADirectoryError: # archive
			zip = ArchiveFile(chapterpath)
			import uuid
			t_p = os.path.join('temp', str(uuid.uuid4()))
			zip.extract_all(t_p)
			filepath = os.path.join(t_p, [x for x in sorted(os.listdir(t_p))\
				if x[-3:] in IMG_FILES][0]) # Find first page
			filepath = os.path.abspath(filepath)
	except FileNotFoundError:
		log.exception('Could not find chapter {}'.format(chapterpath))

	try:
		if not gui_constants.USE_EXTERNAL_VIEWER:
			if sys.platform.startswith('darwin'):
				subprocess.call(('open', filepath))
			elif os.name == 'nt':
				os.startfile(filepath)
			elif os.name == 'posix':
				subprocess.call(('xdg-open', filepath))
		else:
			ext_path = gui_constants.EXTERNAL_VIEWER_PATH
			viewer = external_viewer_checker(ext_path)
			if viewer == 'honeyview':
				subprocess.call((ext_path, filepath))
			else:
				subprocess.check_call((ext_path, filepath))
	except subprocess.CalledProcessError:
		log.exception('Could not open chapter. Invalid external viewer.')
	except:
		log_e('Could not open chapter {}'.format(os.path.split(chapterpath)[1]))

	return None

def tag_to_string(gallery_tag, simple=False):
	"""
	Takes gallery tags and converts it to string, returns string
	if simple is set to True, returns a CSV string, else a dict looking string
	"""
	assert isinstance(gallery_tag, dict), "Please provide a dict like this: {'namespace':['tag1']}"
	string = ""
	if not simple:
		for n, namespace in enumerate(gallery_tag, 1):
			if len(gallery_tag[namespace]) != 0:
				if namespace != 'default':
					string += namespace + ":"

				# find tags
				if namespace != 'default' and len(gallery_tag[namespace]) > 1:
					string += '['
				for x, tag in enumerate(gallery_tag[namespace], 1):
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
		for n, namespace in enumerate(gallery_tag, 1):
			if len(gallery_tag[namespace]) != 0:
				if namespace != 'default':
					string += namespace + ","

				# find tags
				for x, tag in enumerate(gallery_tag[namespace], 1):
					# if we are at the end of the list
					if x == len(gallery_tag[namespace]):
						string += tag
					else:
						string += tag + ', '

				# if we aren't at the end of the list
				if not n == len(gallery_tag):
					string += ', '

	return string

def tag_to_dict(string):
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
				namespace = splitted_tag[0].capitalize()
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

	if title[-4:] in ARCHIVE_FILES:
		title = title[:-4]
	elif title[-3:] is '.7z':
		title = title[:-3]

	parsed_title = {'title':"", 'artist':"", 'language':"other"}
	try:
		a = regex.findall('((?<=\[) *[^\]]+( +\S+)* *(?=\]))', title)
		assert len(a) != 0
		artist = a[0][0].strip()
		parsed_title['artist'] = artist

		try:
			assert a[1]
			lang = ['English', 'Japanese']
			for x in a:
				l = x[0].strip()
				l = l.lower()
				l = l.capitalize()
				if l in lang:
					parsed_title['langauge'] = l
		except IndexError:
			pass

		t = title
		for x in a:
			t = t.replace(x[0], '')

		t = t.replace('[]', '')
		final_title = t.strip()
		parsed_title['title'] = final_title

		return parsed_title
	except AssertionError:
		parsed_title['title'] = title
		return parsed_title

import webbrowser
def open_web_link(url):
	try:
		webbrowser.open_new_tab(url)
	except:
		log_e('Could not open URL in browser')

def open_path(path):
	try:
		if sys.platform.startswith('darwin'):
			subprocess.Popen(['open', path])
		elif os.name == 'nt':
			os.startfile(path)
		elif os.name == 'posix':
			subprocess.Popen(('xdg-open', path))
		else:
			log_e('Could not open path: no OS found')
	except:
		log_e('Could not open path')

def delete_path(path):
	"Deletes the provided recursively"
	if os.path.exists(path):
		error = ''
		try:
			if os.path.isfile:
				os.remove(path)
			else:
				shutil.rmtree(path)
		except PermissionError:
			error = 'PermissionError'

		if error:
			p = os.path.split(path)[1]
			log_e('Failed to delete: {}:{}'.format(error, p))
			return False
		return True


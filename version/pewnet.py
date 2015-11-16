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

import requests, logging, random, time, threading, html, uuid, os
import re as regex
from bs4 import BeautifulSoup
from robobrowser import RoboBrowser
from datetime import datetime
from queue import Queue

from PyQt5.QtCore import QObject, pyqtSignal

import app_constants
import utils

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class WrongURL(Exception): pass

class DownloaderItem(QObject):
	"Convenience class"
	IN_QUEUE, DOWNLOADING, FINISHED, CANCELLED = range(4)
	file_rdy = pyqtSignal(object)
	def __init__(self, url="", session=None):
		super().__init__()
		self.session = session
		self.download_url = url
		self.file = ""
		self.name = ""

		self.total_size = 0
		self.current_size = 0
		self.current_state = self.IN_QUEUE

	def cancel(self):
		self.current_state = self.CANCELLED

	def open(self, containing=False):
		if self.file:
			if containing:
				p = os.path.split(self.file)[0]
				utils.open_path(p, self.file)
			else:
				utils.open_path(self.file)

class Downloader(QObject):
	"""
	A download manager.
	Emits signal item_finished with tuple of url and path to file when a download finishes
	"""
	_inc_queue = Queue()
	_browser_session = None
	_threads = []
	item_finished = pyqtSignal(object)
	active_items = []

	def __init__(self):
		super().__init__()
		# download dir
		self.base = os.path.abspath(app_constants.DOWNLOAD_DIRECTORY)
		if not os.path.exists(self.base):
			os.mkdir(self.base)

	@staticmethod
	def add_to_queue(item, session=None, dir=None):
		"""
		Add a DownloaderItem or url
		An optional requests.Session object can be specified
		A temp dir to be used can be specified

		Returns a downloader item
		"""
		if isinstance(item, str):
			item = DownloaderItem(item)

		log_i("Adding item to download queue: {}".format(item.download_url))
		if dir:
			Downloader._inc_queue.put({'dir':dir, 'item':item})
		else:
			Downloader._inc_queue.put(item)
		Downloader._session = session

		return item

	def _downloading(self):
		"The downloader. Put in a thread."
		while True:
			log_d("Download items in queue: {}".format(self._inc_queue.qsize()))
			print('Starting item download')
			interrupt = False
			item = self._inc_queue.get()
			item.current_state = item.DOWNLOADING
			temp_base = None
			if isinstance(item, dict):
				temp_base = item['dir']
				item = item['item']

			file_name = item.name if item.name else str(uuid.uuid4())
			
			invalid_chars = '\\/:*?"<>|'
			for x in invalid_chars:
				file_name = file_name.replace(x, '')

			file_name = os.path.join(self.base, file_name) if not temp_base else \
				os.path.join(temp_base, file_name)
			file_name_part = file_name + '.part'

			download_url = item.download_url

			self.active_items.append(item)

			if self._browser_session:
				r = self._browser_session.get(download_url, stream=True)
			else:
				r = requests.get(download_url, stream=True)
			item.total_size = int(r.headers['content-length'])

			with open(file_name_part, 'wb') as f:
				for data in r.iter_content(chunk_size=1024):
					if item.current_state == item.CANCELLED:
						interrupt = True
						break
					if data:
						item.current_size += len(data)
						f.write(data)
						f.flush()
			if not interrupt:
				try:
					os.rename(file_name_part, file_name)
				except OSError:
					n = 0
					file_split = os.path.split(file_name)
					while n < 100:
						try:
							if file_split[1]:
								os.rename(file_name_part,
											os.path.join(file_split[0],"({}){}".format(n, file_split[1])))
							else:
								os.rename(file_name_part, "({}){}".format(n, file_name))
							break
						except:
							n += 1
					if n > 100:
						file_name = file_name_part

				item.file = file_name
				item.current_state = item.FINISHED
				item.file_rdy.emit(item)
				self.item_finished.emit(item)
			else:
				try:
					os.remove(file_name_part)
				except:
					pass
			print("finished item download")
			print("items till in queue", self._inc_queue.empty())
			log_d("Finished downloading: {}".format(download_url))
			self.active_items.remove(item)
			self._inc_queue.task_done()

	def start_manager(self, max_tasks):
		"Starts download manager where max simultaneous is mask_tasks"
		log_i("Starting download manager with {} jobs".format(max_tasks))
		for x in range(max_tasks):
			thread = threading.Thread(
					target=self._downloading,
					name='Downloader {}'.format(x),
					daemon=True)
			thread.start()
			self._threads.append(thread)

class HenItem(DownloaderItem):
	"A convenience class that most methods in DLManager and it's subclasses returns"
	thumb_rdy = pyqtSignal(object)
	def __init__(self, session=None):
		super().__init__(session=session)
		self.thumb_url = "" # an url to gallery thumb
		self.thumb = None
		self.cost = "0"
		self.size = ""
		self.metadata = {}
		self.gallery_name = ""
		self.gallery_url = ""
		self.download_type = app_constants.HEN_DOWNLOAD_TYPE
		self.torrents_found = 0
		self.file_rdy.connect(self.check_type)

	def fetch_thumb(self):
		"Fetches thumbnail. Emits thumb_rdy, when done"
		def thumb_fetched():
			self.thumb = self._thumb_item.file
			self.thumb_rdy.emit(self)
		self._thumb_item = Downloader.add_to_queue(self.thumb_url, self.session, app_constants.temp_dir)
		self._thumb_item.file_rdy.connect(thumb_fetched)

	def check_type(self):
		if self.download_type == 1:
			utils.open_torrent(self.file)

	def update_metadata(self, key, value):
		"""
		Recommended way of inserting metadata. Keeps the original EH API response structure
		Remember to call commit_metadata when done!
		"""
		if not self.metadata:
			self.metadata = {
					"gmetadata": [
						{
								"gid":1,
								"title": "",
								"title_jpn": "",
								"category": "Manga",
								"uploader": "",
								"Posted": "",
								"filecount": "0",
								"filesize": 0,
								"expunged": False,
								"rating": "0",
								"torrentcount": "0",
								"tags":[]
							}
						]
				}
		try:
			metadata = self.metadata['gmetadata'][0]
		except KeyError:
			return

		metadata[key] = value

	def commit_metadata(self):
		"Call this method when done updating metadata"
		g_id = 'sample'
		try:
			d_m = {self.metadata['gmetadata'][0]['gid']:g_id}
		except KeyError:
			return
		self.metadata = CommenHen.parse_metadata(self.metadata, d_m)[g_id]

class DLManager(QObject):
	"Base class for site-specific download managers"
	_browser = RoboBrowser(history=True,
						user_agent="Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
						parser='html.parser', allow_redirects=False)
	# download type
	ARCHIVE, TORRENT = False, False
	def __init__(self):
		super().__init__()
		self.ARCHIVE, self.TORRENT = False, False
		if app_constants.HEN_DOWNLOAD_TYPE == 0:
			self.ARCHIVE = True
		elif app_constants.HEN_DOWNLOAD_TYPE == 1:
			self.TORRENT = True

	def _error(self):
		pass

	def from_gallery_url(self, url):
		"""
		Needs to be implemented in site-specific subclass
		URL checking  and class instantiating is done in GalleryDownloader class in io_misc.py
		Basic procedure for this method:
		- open url with self._browser and do the parsing
		- create HenItem and fill out it's attributes
		- specify download type (important)... 0 for archive and 1 for torrent 2 for other
		- fetch optional thumbnail on HenItem
		- set download url on HenItem (important)
		- add h_item to download queue
		- return h-item if everything went successfully, else return none

		Metadata should imitiate the offical EH API response.
		It is recommended to use update_metadata in HenItem when adding metadata
		see the ChaikaManager class for a complete example
		EH API: http://ehwiki.org/wiki/API
		"""
		raise NotImplementedError

class ChaikaManager(DLManager):
	"panda.chaika.moe manager"

	def __init__(self):
		super().__init__()
		self.url = 'http://panda.chaika.moe/'

	def from_gallery_url(self, url):
		h_item = HenItem(self._browser.session)
		h_item.download_type = 0
		
		if '/gallery/' in url:
			a_url = self._gallery_page(url, h_item)
			self._archive_page(a_url, h_item)
		elif '/archive' in url:
			g_url = self._archive_page(url, h_item)
			self._gallery_page(g_url, h_item)
		else:
			return 
		h_item.commit_metadata()
		h_item.name = h_item.gallery_name+'.zip'
		Downloader.add_to_queue(h_item, self._browser.session)
		return h_item

	def _gallery_page(self, g_url, h_item):
		"Returns url to archive and updates h_item metadata from the /gallery/g_id page"
		self._browser.open(g_url)

		all_li = self._browser.find_all('li')

		title = all_li[0].text.split(':')[1]
		h_item.update_metadata('title', title)
		jpn_title = all_li[1].text.split(':')[1]
		h_item.update_metadata('title_jpn', jpn_title)
		type = all_li[2].text.split(':')[1]
		h_item.update_metadata('category', type)
		rating = all_li[3].text.split(':')[1]
		h_item.update_metadata('rating', rating)
		f_count = all_li[4].text.split(':')[1]
		h_item.update_metadata('filecount', f_count)
		f_size_in_mb = all_li[5].text.split(':')[1]
		f_size_in_bytes = int(float(f_size_in_mb.replace('MB', '').strip()) * 1048576)
		h_item.update_metadata('filesize', f_size_in_bytes)
		posted = all_li[7].text.split(':')[1]
		posted = posted.replace('.', '').replace(',', '')
		month, day, year = posted.split(' ')
		# sigh.. Sep abbreviated as Sept.. really?!?
		if month.startswith('Jan'):
			month = '01'
		elif month.startswith('Feb'):
			month = '02'
		elif month.startswith('Mar'):
			month = '03'
		elif month.startswith('Apr'):
			month = '04'
		elif month.startswith('May'):
			month = '05'
		elif month.startswith('Jun'):
			month = '06'
		elif month.startswith('Jul'):
			month = '07'
		elif month.startswith('Aug'):
			month = '08'
		elif month.startswith('Sep'):
			month = '09'
		elif month.startswith('Oct'):
			month = '10'
		elif month.startswith('Nov'):
			month = '11'
		elif month.startswith('Dec'):
			month = '12'
		posted = time.mktime(datetime.strptime(month+day+year, '%m%d%Y').timetuple())
		h_item.update_metadata('posted', posted)

		h_item.gallery_name = title
		h_item.size = f_size_in_mb

		archive_page = all_li[len(all_li)-1].a.get('href')
		archive_page_url = self.url + archive_page[1:]
		return archive_page_url

	def _archive_page(self, a_url, h_item):
		"Returns url to gallery and updates h_item metadata from the /archive/a_id page"
		self._browser.open(a_url)		
		all_li = self._browser.find_all('li')

		EPG = all_li[3].text.split('>>') # e-link, posted, g-link

		gallery_url = self.url + EPG[2].replace('Gallery link:', '').strip()[1:] # unreadable? sorry
		h_item.gallery_url = gallery_url

		tags = []
		ns_tags_li = all_li[4].ul.find_all('li')
		for nt in ns_tags_li:
			# namespace
			ns = nt.find('label')
			ns = ns.text.replace('_', ' ') if ns else ''
			# tags
			all_tags = nt.find_all('a')
			for t in all_tags:
				tag = t.text.replace('_', ' ')
				tags.append(ns + tag)
		h_item.update_metadata('tags', tags)

		archive = self._browser.find('li', {'class':'pagination_cen'}).a.get('href')
		archive_url = self.url + archive[1:]
		h_item.download_url = archive_url
		return gallery_url

class HenManager(DLManager):
	"G.e or Ex gallery manager"

	def __init__(self):
		super().__init__()
		self.e_url = 'http://g.e-hentai.org/'

	def _archive_url_d(self, gid, token, key):
		"Returns the archiver download url"
		base = self.e_url + 'archiver.php?'
		d_url = base + 'gid=' + str(gid) + '&token=' + token + '&or=' + key
		return d_url

	def _torrent_url_d(self, gid, token):
		"Returns the torrent download url and filename"
		base = self.e_url + 'gallerytorrents.php?'
		torrent_page = base + 'gid=' + str(gid) + '&t=' + token
		self._browser.open(torrent_page)
		torrents = self._browser.find_all('table')
		if not torrents:
			return
		torrent = None # [seeds, url, name]
		for t in torrents:
			parts = t.find_all('tr')
			# url & name
			url = parts[2].td.a.get('href')
			name = parts[2].td.a.text + '.torrent'

			# seeds peers etc... NOT uploader
			meta = [x.text for x in parts[0].find_all('td')]
			seed_txt = meta[3]
			# extract number
			seeds = int(seed_txt.split(' ')[1])

			if not torrent:
				torrent = [seeds, url, name]
			else:
				if seeds > torrent[0]:
					torrent = [seeds, url, name]

		_, url, name = torrent # just get download url

		# TODO: make user choose?
		return url, name

	def from_gallery_url(self, g_url):
		"""
		Finds gallery download url and puts it in download queue
		"""
		if 'ipb_member_id' in self._browser.session.cookies and \
			'ipb_pass_hash' in self._browser.session.cookies:
			hen = ExHen(self._browser.session.cookies['ipb_member_id'],
			   self._browser.session.cookies['ipb_pass_hash'])
		else:
			hen = EHen()

		api_metadata, gallery_gid_dict = hen.add_to_queue(g_url, True, False)
		gallery = api_metadata['gmetadata'][0]

		h_item = HenItem(self._browser.session)
		h_item.gallery_url = g_url
		h_item.metadata = CommenHen.parse_metadata(api_metadata, gallery_gid_dict)
		try:
			h_item.metadata = h_item.metadata[g_url]
		except KeyError:
			raise WrongURL
		h_item.thumb_url = gallery['thumb']
		h_item.gallery_name = gallery['title']
		h_item.size = "{0:.2f} MB".format(gallery['filesize']/1048576)

		if self.ARCHIVE:
			h_item.download_type = 0
			d_url = self._archive_url_d(gallery['gid'], gallery['token'], gallery['archiver_key'])

			# ex/g.e
			self._browser.open(d_url)
			download_btn = self._browser.get_form()
			if download_btn:
				f_div = self._browser.find('div', id='db')
				divs = f_div.find_all('div')
				h_item.cost = divs[0].find('strong').text
				h_item.size = divs[1].find('strong').text
				self._browser.submit_form(download_btn)
			# get dl link
			dl = self._browser.find('a').get('href')
			self._browser.open(dl)
			succes_test = self._browser.find('p')
			if succes_test and 'successfully' in succes_test.text:
				gallery_dl = self._browser.find('a').get('href')
				gallery_dl = self._browser.url.split('/archive')[0] + gallery_dl
				f_name = succes_test.find('strong').text
				h_item.download_url = gallery_dl
				h_item.fetch_thumb()
				h_item.name = f_name
				Downloader.add_to_queue(h_item, self._browser.session)
				return h_item

		elif self.TORRENT:
			h_item.download_type = 1
			h_item.torrents_found = int(gallery['torrentcount'])
			h_item.fetch_thumb()
			if  h_item.torrents_found > 0:
				g_id_token = CommenHen.parse_url(g_url)
				url_and_file = self._torrent_url_d(g_id_token[0], g_id_token[1])
				if url_and_file:
					h_item.download_url = url_and_file[0]
					h_item.name = url_and_file[1]
					Downloader.add_to_queue(h_item, self._browser.session)
					return h_item
			else:
				return h_item
		return False

class ExHenManager(HenManager):
	"ExHentai Manager"
	def __init__(self, ipb_id, ipb_pass):
		super().__init__()
		cookies = {'ipb_member_id':ipb_id,
				  'ipb_pass_hash':ipb_pass}
		self._browser.session.cookies.update(cookies)
		self.e_url = "http://exhentai.org/"



class CommenHen:
	"Contains common methods"
	LOCK = threading.Lock()
	TIME_RAND = app_constants.GLOBAL_EHEN_TIME
	QUEUE = []
	COOKIES = {}
	LAST_USED = time.time()
	HEADERS = {'user-agent':"Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0"}

	@staticmethod
	def hash_search(g_hash):
		"""
		Searches ex or g.e for a gallery with the hash value
		Return list with titles of galleries found.
		"""
		raise NotImplementedError

	def begin_lock(self):
		log_d('locked')
		self.LOCK.acquire()
		t1 = time.time()
		while int(time.time() - self.LAST_USED) < 4:
			t = random.randint(4, self.TIME_RAND)
			time.sleep(t)
		t2 = time.time() - t1
		log_d("Slept for {}".format(t2))
	
	def end_lock(self):
		log_d('unlocked')
		self.LAST_USED = time.time()
		self.LOCK.release()

	def add_to_queue(self, url, proc=False, parse=True):
		"""Add url the the queue, when the queue has reached 25 entries will auto process
		:proc -> proccess queue
		:parse -> return parsed metadata
		"""
		self.QUEUE.append(url)
		log_i("Status on queue: {}/25".format(len(self.QUEUE)))
		if proc:
			if parse:
				return CommenHen.parse_metadata(*self.process_queue())
			return self.process_queue()
		if len(self.QUEUE) > 24:
			if parse:
				return CommenHen.parse_metadata(*self.process_queue())
			return self.process_queue()
		else:
			return 0

	def process_queue(self):
		"""
		Process the queue if entries exists, deletes entries.
		Note: Will only process 25 entries (first come first out) while
			additional entries will get deleted.
		"""
		log_i("Processing queue...")
		if len(self.QUEUE) < 1:
			return None

		if len(self.QUEUE) > 25:
			api_data, galleryid_dict = self.get_metadata(self.QUEUE[:25])
		else:
			api_data, galleryid_dict = self.get_metadata(self.QUEUE)

		log_i("Flushing queue...")
		self.QUEUE.clear()
		return api_data, galleryid_dict

	def check_cookie(self, cookie):
		assert isinstance(cookie, dict)
		cookies = self.COOKIES.keys()
		present = []
		for c in cookie:
			if c in cookies:
				present.append(True)
			else:
				present.append(False)
		if not all(present):
			log_i("Updating cookies...")
			self.COOKIES.update(cookie)

	def handle_error(self, response):
		content_type = response.headers['content-type']
		text = response.text
		if 'image/gif' in content_type:
			app_constants.NOTIF_BAR.add_text('Provided exhentai credentials are incorrect!')
			log_e('Provided exhentai credentials are incorrect!')
			time.sleep(5)
			return False
		elif 'text/html' and 'Your IP address has been' in text:
			app_constants.NOTIF_BAR.add_text("Your IP address has been temporarily banned from g.e-/exhentai")
			log_e('Your IP address has been temp banned from g.e- and ex-hentai')
			time.sleep(5)
			return False
		elif 'text/html' in content_type and 'You are opening' in text:
			time.sleep(random.randint(10,50))
		return True

	@staticmethod
	def parse_url(url):
		"Parses url into a list of gallery id and token"
		gallery_id = int(regex.search('(\d+)(?=\S{4,})', url).group())
		gallery_token = regex.search('(?<=\d/)(\S+)(?=/$)', url).group()
		parsed_url = [gallery_id, gallery_token]
		return parsed_url

	@staticmethod
	def parse_metadata(metadata_json, dict_metadata):
		"""
		:metadata_json <- raw data provided by E-H API
		:dict_metadata <- a dict with gallery id's as keys and url as value

		returns a dict with url as key and gallery metadata as value
		"""
		def invalid_token_check(g_dict):
			if 'error' in g_dict:
				return False
			else: return True

		parsed_metadata = {}
		for gallery in metadata_json['gmetadata']:
			url = dict_metadata[gallery['gid']]
			if invalid_token_check(gallery):
				new_gallery = {}
				def fix_titles(text):
					t = html.unescape(text)
					t = " ".join(t.split())
					return t
				try:
					gallery['title_jpn'] = fix_titles(gallery['title_jpn'])
					gallery['title'] = fix_titles(gallery['title'])
					new_gallery['title'] = {'def':gallery['title'], 'jpn':gallery['title_jpn']}
				except KeyError:
					gallery['title'] = fix_titles(gallery['title'])
					new_gallery['title'] = {'def':gallery['title']}

				new_gallery['type'] = gallery['category']
				new_gallery['pub_date'] = datetime.fromtimestamp(int(gallery['posted']))
				tags = {'default':[]}
				for t in gallery['tags']:
					if ':' in t:
						ns_tag = t.split(':')
						namespace = ns_tag[0].capitalize()
						tag = ns_tag[1].lower()
						if not namespace in tags:
							tags[namespace] = []
						tags[namespace].append(tag)
					else:
						tags['default'].append(t.lower())
				new_gallery['tags'] = tags
				parsed_metadata[url] = new_gallery
			else:
				log_e("Error in received response with URL: {}".format(url))

		return parsed_metadata

	def get_metadata(self, list_of_urls, cookies=None):
		"""
		Fetches the metadata from the provided list of urls
		through the official API.
		returns raw api data and a dict with gallery id as key and url as value
		"""
		assert isinstance(list_of_urls, list)
		if len(list_of_urls) > 25:
			log_e('More than 25 urls are provided. Aborting.')
			return None

		payload = {"method": "gdata",
			 "gidlist": [],
			 "namespace": 1
			 }
		dict_metadata = {}
		for url in list_of_urls:
			parsed_url = CommenHen.parse_url(url.strip())
			dict_metadata[parsed_url[0]] = url # gallery id
			payload['gidlist'].append(parsed_url)

		if payload['gidlist']:
			self.begin_lock()
			if cookies:
				self.check_cookie(cookies)
				r = requests.post(self.e_url, json=payload, timeout=30, headers=self.HEADERS, cookies=self.COOKIES)
			else:
				r = requests.post(self.e_url, json=payload, timeout=30, headers=self.HEADERS)
			if not self.handle_error(r):
				return 'error'
			self.end_lock()
		else: return None
		try:
			r.raise_for_status()
		except:
			log.exception('Could not fetch metadata: connection error')
			return None
		return r.json(), dict_metadata

	def eh_hash_search(self, hash_string, cookies=None):
		"""
		Searches ehentai for the provided string or list of hashes,
		returns a dict with hash:[list of title,url tuples] of hits found or emtpy dict if no hits are found.
		"""
		assert isinstance(hash_string, (str, list))
		if isinstance(hash_string, str):
			hash_string = [hash_string]

		def no_hits_found_check(html):
			"return true if hits are found"
			soup = BeautifulSoup(html, "html.parser")
			f_div = soup.body.find_all('div')
			for d in f_div:
				if 'No hits found' in d.text:
					return False
			return True

		hash_url = app_constants.DEFAULT_EHEN_URL + '?f_shash='
		found_galleries = {}
		log_i('Initiating hash search on ehentai')
		for h in hash_string:
			log_d('Hash search: {}'.format(h))
			self.begin_lock()
			if cookies:
				self.check_cookie(cookies)
				r = requests.get(hash_url+h, timeout=30, headers=self.HEADERS, cookies=self.COOKIES)
			else:
				r = requests.get(hash_url+h, timeout=30, headers=self.HEADERS)
			self.end_lock()
			if not self.handle_error(r):
				return 'error'
			if not no_hits_found_check(r.text):
				log_e('No hits found with hash: {}'.format(h))
				continue
			soup = BeautifulSoup(r.text, "html.parser")
			log_i('Parsing html')
			try:
				if soup.body:
					found_galleries[h] = []
					# list view or grid view
					type = soup.find(attrs={'class':'itg'}).name
					if type == 'div':
						visible_galleries = soup.find_all('div', attrs={'class':'id1'})
					elif type == 'table':
						visible_galleries = soup.find_all('div', attrs={'class':'it5'})
				
					log_i('Found {} visible galleries'.format(len(visible_galleries)))
					for gallery in visible_galleries:
						title = gallery.text
						g_url = gallery.a.attrs['href']
						found_galleries[h].append((title,g_url))
			except AttributeError:
				log.exception('Unparseable html')
				log_d("\n{}\n".format(soup.prettify()))
				continue

		if found_galleries:
			log_i('Found {} out of {} galleries'.format(len(found_galleries), len(hash_string)))
			return found_galleries
		else:
			log_w('Could not find any galleries')
			return {}

	def eh_gallery_parser(self, url, cookies=None):
		"""
		Parses an ehentai page for metadata.
		Returns gallery dict with following metadata:
		- title
		- jap_title
		- type
		- language
		- publication date
		- namespace & tags
		"""
		self.begin_lock()
		if cookies:
			self.check_cookie(cookies)
			r = requests.get(url, headers=self.HEADERS, timeout=30, cookies=self.COOKIES)
		else:
			r = requests.get(url, headers=self.HEADERS, timeout=30)
		self.end_lock()
		if not self.handle_error(r):
			return {}
		html = r.text
		if len(html)<5000:
			log_w("Length of HTML response is only {} => Failure".format(len(html)))
			return {}

		gallery = {}
		soup = BeautifulSoup(html)

		#title
		div_gd2 = soup.body.find('div', id='gd2')
		# normal
		title = div_gd2.find('h1', id='gn').text.strip()
		# japanese
		jap_title = div_gd2.find('h1', id='gj').text.strip()

		gallery['title'] = title
		gallery['jap_title'] = jap_title

		# Type
		div_gd3 = soup.body.find('div', id='gd3')
		gallery['type'] = div_gd3.find('img').get('alt')

		# corrects name
		if gallery['type'] == 'artistcg':
			gallery['type'] = 'artist cg sets'
		elif gallery['type'] == 'imageset':
			gallery['type'] = 'image sets'
		elif gallery['type'] == 'gamecg':
			gallery['type'] = 'game cg sets'
		elif gallery['type'] == 'asianporn':
			gallery['type'] = 'asian porn'

		# Language
		lang_tag = soup.find('td', text='Language:').next_sibling
		lang = lang_tag.text.split(' ')[0]
		gallery['language'] = lang

		# Publication date
		pub_tag = soup.find('td', text='Posted:').next_sibling
		pub_date = datetime.strptime(pub_tag.text.split(' ')[0], '%Y-%m-%d').date()
		gallery['published'] = pub_date

		# Namespace & Tags
		found_tags = {}
		def tags_in_ns(tags):
			return not tags.has_attr('class')
		tag_table = soup.find('div', id='taglist').next_element
		namespaces = tag_table.find_all('tr')
		for ns in namespaces:
			namespace = ns.next_element.text.replace(':', '')
			namespace = namespace.capitalize()
			found_tags[namespace] = []
			tags = ns.find(tags_in_ns).find_all('div')
			for tag in tags:
				found_tags[namespace].append(tag.text)

		gallery['tags'] = found_tags
		return gallery

class ExHen(CommenHen):
	"Fetches gallery metadata from exhen"
	def __init__(self, cookie_member_id, cookie_pass_hash):
		self.cookies = {'ipb_member_id':cookie_member_id,
				  'ipb_pass_hash':cookie_pass_hash}
		self.e_url = "http://exhentai.org/api.php"

	def get_metadata(self, list_of_urls):
		return super().get_metadata(list_of_urls, self.cookies)

	def eh_gallery_parser(self, url):
		return super().eh_gallery_parser(url, self.cookies)

	def eh_hash_search(self, hash_string):
		return super().eh_hash_search(hash_string, self.cookies)

class EHen(CommenHen):
	"Fetches galleries from ehen"
	def __init__(self):
		self.e_url = "http://g.e-hentai.org/api.php"


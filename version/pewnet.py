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

import requests, logging, random, time, pickle, os, threading
import re as regex
from bs4 import BeautifulSoup
from datetime import datetime
from .gui import gui_constants
from PyQt5.QtCore import QObject, pyqtSignal

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class CommenHen:
	"Contains common methods"
	LOCK = threading.Lock()
	TIME_RAND = gui_constants.GLOBAL_EHEN_TIME
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

	def add_to_queue(self, url, proc=False):
		"Add url the the queue, when the queue has reached 25 entries will auto process"
		self.QUEUE.append(url)
		log_i("Status on queue: {}/25".format(len(self.QUEUE)))
		if proc:
			return self.process_queue()
		if len(self.QUEUE) > 24:
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
			data = self.get_metadata(self.QUEUE[:25])
		else:
			data = self.get_metadata(self.QUEUE)

		log_i("Flushing queue...")
		self.QUEUE.clear()
		return data

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
			gui_constants.NOTIF_BAR.add_text('Provided exhentai credentials are incorrect!')
			log_e('Provided exhentai credentials are incorrect!')
			time.sleep(5)
			return False
		elif 'text/html' and 'Your IP address has been' in text:
			gui_constants.NOTIF_BAR.add_text("Your IP address has been temporarily banned from g.e-/exhentai")
			log_e('Your IP address has been temp banned from g.e- and ex-hentai')
			time.sleep(5)
			return False
		elif 'text/html' in content_type and 'You are opening' in text:
			time.sleep(random.randint(10,50))
		return True

	def parse_url(self, url):
		"Parses url into a list of gallery id and token"
		gallery_id = int(regex.search('(\d+)(?=\S{4,})', url).group())
		gallery_token = regex.search('(?<=\d/)(\S+)(?=/$)', url).group()
		parsed_url = [gallery_id, gallery_token]
		return parsed_url

	def parse_metadata(self, metadata_json, dict_metadata):

		def invalid_token_check(g_dict):
			if 'error' in g_dict:
				return False
			else: return True

		parsed_metadata = {}
		for gallery in metadata_json['gmetadata']:
			if invalid_token_check(gallery):
				new_gallery = {}
				try:
					new_gallery['title'] = {'def':gallery['title'], 'jpn':gallery['title_jpn']}
				except KeyError:
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
				url = dict_metadata[gallery['gid']]
				parsed_metadata[url] = new_gallery
			else:
				log_e("Error in received response with URL: {}".format(url))

		return parsed_metadata

	def get_metadata(self, list_of_urls, cookies=None):
		"""
		Fetches the metadata from the provided list of urls
		through the official API.
		If the povided list of urls contains more than 1 url,
		a dict will be returned with url as key and tags as value
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
			parsed_url = self.parse_url(url.strip())
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
		metadata = self.parse_metadata(r.json(), dict_metadata)
		return metadata

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

		hash_url = gui_constants.DEFAULT_EHEN_URL + '?f_shash='
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
	"Fetches galleries from exhen"
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


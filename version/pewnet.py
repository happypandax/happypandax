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

import requests, logging
import re as regex

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class CommenHen:
	"Contains common methods"
	SESSION = requests.Session()

	def parse_url(self, url):
		"Parses url into a list of gallery id and token"
		series_id = int(regex.search('(\d+)(?=\S{4,})', url).group())
		gallery_token = regex.search('(?<=\d/)(\S+)(?=/$)', url).group()
		parsed_url = [series_id, gallery_token]
		return parsed_url

	def parse_metadata(self, metadata_dict):

		def invalid_token_check(g_dict):
			if 'error' in g_dict:
				return False
			else: return True

		parsed_metadata = []
		for gallery in metadata_dict['gmetadata']:
			if invalid_token_check(gallery):
				parsed_metadata.append(gallery)

		return parsed_metadata

	def get_metadata(self, list_of_urls):
		"""
		Fetches the metadata from the provided list of urls
		through the official API
		"""
		assert isinstance(list_of_urls, list)
		try:
			assert len(list_of_urls) <= 25
		except AssertionError:
			return None

		payload = {"method": "gdata",
			 "gidlist": []
			 }
		for url in list_of_urls:
			parsed_url = self.parse_url(url.strip())
			payload['gidlist'].append(parsed_url)

		if payload['gidlist']:
			try:
				r = self.SESSION.post(self.e_url, cookies=self.cookies, json=payload)
			except NameError:
				r = self.SESSION.post(self.e_url, json=payload)
		else: return None
		try:
			log.exception('Could not fetch metadata')
			r.raise_for_status()
		except: # TODO: bad..bad..bad... improve this!!
			return None
		metadata = self.parse_metadata(r.json())
		return metadata

	def eh_html_parser(self, url, cookies=None):
		"""
		Parses an ehentai page for metadata.
		Returns gallery dict with following metadata:
		- Type
		- Language
		- Publication Date
		- Namespace & Tags
		"""
		if cookies:
			r = requests.get(url, cookies=cookies, timeout=30)
		else:
			r = requests.get(url, timeout=30)
		html = r.text
		if len(html)<5000:
			log_w("Length of HTML response is only {} => Failure".format(len(html)))
			return {}

		gallery = {}
		soup = BeautifulSoup(html)
		with open('html2.html', 'w', encoding='utf-8') as f:
			f.write(soup.prettify())
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

	def eh_html_parser(self, url):
		super().eh_html_parser(url, self.cookies)

class EHen(CommenHen):
	"Fetches galleries from ehen"
	def __init__(self):
		self.e_url = "http://g.e-hentai.org/api.php"


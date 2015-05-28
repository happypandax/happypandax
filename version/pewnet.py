import requests
import re as regex

class CommenHen:
	"Contains common methods"
	SESSION = requests.Session()
	def get_metadata(self, list_of_urls):
		raise NotImplementedError

	def parse_url(self, url):
		"Parses url into a list of gallery id and token"
		gallery_id = int(regex.search('(\d+)(?=\S{4,})', url).group())
		gallery_token = regex.search('(?<=\d/)(\S+)(?=/$)', url).group()
		parsed_url = [gallery_id, gallery_token]
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

class ExHen(CommenHen):
	"Fetches galleries from exhen"
	def __init__(self, cookie_member_id, cookie_pass_hash):
		self.cookies = {'ipb_member_id':cookie_member_id,
				  'ipb_pass_hash':cookie_pass_hash}
		self.e_url = "http://exhentai.org/api.php"

	def get_metadata(self, list_of_urls):
		"Fetches the metadata from the provided list of urls" 
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
			r = self.SESSION.post(self.e_url, cookies=self.cookies, json=payload)
		else: return None
		try:
			r.raise_for_status()
		except: # TODO: bad..bad..bad... improve this!!
			return None
		metadata = self.parse_metadata(r.json())
		return metadata

class EHen(CommenHen):
	"Fetches galleries from ehen"
	def __init__(self):
		self.e_url = "http://g.e-hentai.org/api.php"

	def get_metadata(self, list_of_urls):
		"Fetches the metadata from the provided list of urls" 
		assert isinstance(list_of_urls, list)
		assert len(list_of_urls) <= 25

		payload = {"method": "gdata",
			 "gidlist": []
			 }

		for url in list_of_urls:
			parsed_url = self.parse_url(url.strip())
			payload['gidlist'].append(parsed_url)

		if payload['gidlist']:
			r = self.SESSION.post(self.e_url, json=payload)
		else: return None
		try:
			r.raise_for_status()
		except: # TODO: bad..bad..bad... improve this!!
			return None

		metadata = self.parse_metadata(r.json())
		return metadata

#go = ExHen(id, hash)
#u1 = 'http://g.e-hentai.org/g/618395/0439fa3666/ '
#u2 = 'http://g.e-hentai.org/g/817727/08056b3040/'

#x1 = 'http://exhentai.org/g/817738/c556146890/'
#x2 = 'http://exhentai.org/g/817702/aa68011fff/'

#m = go.get_metadata([x1, x2])
#pprint.pprint(m)


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
import json

class Settings:
	def __init__(self):
		self.ini = {
				'ipb_id':'',
				'ipb_pass':'',
			}

		try:
			with open('settings.json', 'x') as f:
				pass
		except FileExistsError:
			with open('settings.json', 'r', encoding='utf-8') as f:
				try:
					self.ini = json.load(f)
				except:
					pass

	def set_ipb(self, id, pass_hash):
		self.ini['ipb_id'] = id
		self.ini['ipb_pass'] = pass_hash

		with open('settings.json', 'w', encoding='utf-8') as f:
			json.dump(self.ini, f)

	def get_ipb(self):
		return self.ini


s = Settings()
def exhen_cookies():
	cookies = [s.ini['ipb_id'], s.ini['ipb_pass']]
	return cookies
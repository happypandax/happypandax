class Settings:
	def __init__(self):
		self. ini = {
				'ipb_id':'',
				'ipb_pass':'',
			}

s = Settings()
def exhen_cookies():
	cookies = [s.ini['ipb_id'], s.ini['ipb_pass']]
	return cookies
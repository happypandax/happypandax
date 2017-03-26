class HPlugin:
	ID = "3acf4958-d010-4dbd-a600-5a195559031a"
	NAME = "Test Plugin"
	AUTHOR = "Pew"
	DESCRIPTION = "Test desc"
	VERSION = (0, 0, 1)

	REQUIRE = [
		("9fb4ce2a-fe47-42ef-8c58-e039d999eb19", (0, 0, 1))
	]

	def __init__(self, *args, **kwargs):
		self.core_id = "9fb4ce2a-fe47-42ef-8c58-e039d999eb19"
		self.core = self.connect_plugin(self.core_id)
		self.core.hello()
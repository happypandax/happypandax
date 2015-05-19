import time, datetime, os, subprocess, sys

IMG_FILES =  ['jpg','bmp','png','gif']

def today():
	"Returns current date in a list: [dd, Mmm, yyyy]"
	_date = datetime.date.today()
	day = _date.strftime("%d")
	month = _date.strftime("%b")
	year = _date.strftime("%Y")
	return [day, month, year]

def exception_handler(msg):
	"Spawns a dialog with the specified msg"
	pass

def open(chapterpath):

	filepath = os.path.join(chapterpath, [x for x in sorted(os.listdir(chapterpath))\
		if x[-3:] in IMG_FILES][0]) # Find first page

	if sys.platform.startswith('darwin'):
		subprocess.call(('open', filepath))
	elif os.name == 'nt':
		os.startfile(filepath)
	elif os.name == 'posix':
		subprocess.call(('xdg-open', filepath))

def tag_to_string(series_tag):
	"Takes series tags and converts it to string, returns string"
	assert isinstance(series_tag, dict), "Please provide a dict like this: {'namespace':['tag1']}"
	string = ""
	for n, namespace in enumerate(series_tag, 1):
		string += namespace + ":"

		# find tags
		if len(series_tag[namespace]) > 1:
			string += '['
		for x, tag in enumerate(series_tag[namespace], 1):
			# if we are at the end of the list
			if x == len(series_tag[namespace]):
				string += tag
			else:
				string += tag + ', '
		if len(series_tag[namespace]) > 1:
			string += ']'

		# if we aren't at the end of the list
		if not n == len(series_tag):
			string += ', '
	return string

def tag_to_dict(string):
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

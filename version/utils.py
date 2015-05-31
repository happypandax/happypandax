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

import time, datetime, os, subprocess, sys

IMG_FILES =  ['jpg','bmp','png','gif']

def today():
	"Returns current date in a list: [dd, Mmm, yyyy]"
	_date = datetime.date.today()
	day = _date.strftime("%d")
	month = _date.strftime("%b")
	year = _date.strftime("%Y")
	return [day, month, year]


from PyQt5.QtWidgets import QMessageBox
from sys import exit

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
		if len(series_tag[namespace]) != 0:
			if namespace != 'default':
				string += namespace + ":"

			# find tags
			if namespace != 'default' and len(series_tag[namespace]) > 1:
				string += '['
			for x, tag in enumerate(series_tag[namespace], 1):
				# if we are at the end of the list
				if x == len(series_tag[namespace]):
					string += tag
				else:
					string += tag + ', '
			if namespace != 'default' and len(series_tag[namespace]) > 1:
				string += ']'

			# if we aren't at the end of the list
			if not n == len(series_tag):
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
	webbrowser.open_new_tab(url)
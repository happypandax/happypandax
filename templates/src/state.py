
state = {
    'title': 'HPX - Alpha',
    'app': None,
    'history': None,  # router history
    'container_ref': None,  # main conatiner
    'commands': set(),
    'debug': False,
    'new_update': False,
    'active': True,  # current page is active
    'connected': True,
    'accepted': False,  # logged in
    'guest_allowed': False,
    'version': {},
    'locales': {},  # locales from server
    'untranslated_text': False,
    'translation_id_error': False,
    'translations': None,
    'reset_scroll': True,
}

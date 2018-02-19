
state = {
    'app': None,
    'container_ref': None,  # main conatiner
    'commands': set(),
    'debug': True,
    'new_update': False,
    'active': True,  # current page is active
    'connected': True,
    'locales': {},  # locales from server
    'untranslated_text': False,
    'translation_id_error': False,
}

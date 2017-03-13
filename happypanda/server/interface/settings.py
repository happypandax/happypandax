from happypanda.common import constants, message

def set_settings(namespace, set_dict={}):
    """
    Set settings

    Params:
        - set_dict -- a dictionary containing key:value pairs :D

    Returns:
        Status
    """
    return message.Message("works")

def get_settings(namespace, set_list=[]):
    """
    Set settings
    Use setting key 'all' to fetch all setting key:values

    Params:
        - set_list -- a list of setting keys

    Returns:
        dict of setting_key:value
    """
    return message.Message("works")


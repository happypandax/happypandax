from happypanda.common import constants, message

def set_settings(settings={}, ctx=None):
    """
    Set settings

    Params:
        - settings -- a dictionary containing key:value pairs

    Returns:
        Status
    """


    return message.Message("ok")

def get_settings(settings=[], ctx=None):
    """
    Set settings
    Use setting key 'all' to fetch all setting key:values

    Params:
        - set_list -- a list of setting keys

    Returns:
        dict of setting_key:value
    """
    return message.Message("works")


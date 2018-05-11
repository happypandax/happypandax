Translations
========================================

It is possible to translate and localize HPX into your language.

Existing translations can be found at ``[HPX]/translations``.
These translation files are named like so: ``<language_code>.<namespace>.yaml`` in all lower-case.

In these translation files, translations are distinguished by **translation ids**:

.. code-block:: guess

    translation-id: translated text
    translation-id-2: translated text 2
    ...


It is required that for every language, a namespace called ``general`` exists with this **translation id**:

.. code-block:: guess

    locale: LanguageName (Country)

You can see ``translations/en_us.general.yaml`` for an example.

If you need a quick primer on YAML, see `here <https://learn.getgrav.org/advanced/yaml>`_.

Translator's perspective
-------------------------------------

If you're coming from a translator's perspective and just want to translate then here are some quick pointers.

It is recommended that you translate from the ``en_us`` language code as this is the default language code for HPX , and
also the one being kept up to date the most and fastest.

When translating you should take note of the ``_version_`` id from the file you're translating from at the time of translating.
When you're done translating, you update the ``_version_`` in your translation files to match the ones you were translating from.
This way you'' know that your translation files are out of date when these ``_version_``'s differ.

You can (and should!) submit your translation files to the main repo. Just create a pull request and it'll be merged and usable by everyone in future releases!

If you're going to translate the ``ui`` namespace, do note the prefixes on the **language ids** and their meaning:

.. code-block:: guess

    #  Prefixes:
    #	- mi == menu item text	
    #	- h == header text
    #	- de == description text
    #	- t == normal text
    #	- b == button text

I might create a tool (or you can too) for helping translating later if I have time.

Developer's perspective
-------------------------------------

Developers can choose to create their own language namespace for their own client applications if they desire.
This language namespace can also be included in future HPX releases. Just create a pull request.

Say I made an app client for HPX named ``myapp``. For this app I could create language files with the namespace ``myapp`` and include them in HPX.
Others can then come edit or create their own translations for my app in the same manner as they would for HPX.

Translations are used like this ``<namespace>.<translation_id>``.
For example: ``"general.locale"`` resolves to ``English (United States)``. 

If you're building a client, you can access these translations through the server API functions :py:func:`.ui.translate` and :py:func:`.meta.get_locales`.

Keep in mind that the locale settings for HPX are *client-scoped*, meaning that you can change the locale settings from a client freely without interfering with other client's locale settings.

.. todo::

    accessing through plugins
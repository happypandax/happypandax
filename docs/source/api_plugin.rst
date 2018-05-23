Plugin API
========================================

.. automodule:: happypanda.core.plugin_interface
   :members:
   :member-order: groupwise

Commands
----------------------------------------

.. automodule:: happypanda.core.commands.meta_cmd

.. exec::
    from sphinx.util import inspect as sinspect
    from happypanda.core.commands import database_cmd
    import inspect
    mod = database_cmd
    cls_str = """.. py:class:: {}{}
    {}
        **Return type:** {}       

        **Available entries:**
        {}
        **Available events:**
        {}
    """
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if obj.__module__ == mod.__name__:
            if getattr(obj, 'main'):
                sig = sinspect.Signature(obj.main, bound_method=True)
            else:
                sig = sinspect.Signature(obj.__init__, bound_method=True)
            retval = sig.signature.return_annotation
            sig.signature = sig.signature.replace(return_annotation=inspect.Signature.empty)
            print(cls_str.format(name, sig.format_args(), obj.__doc__, retval, '', ''))

.. automodule:: happypanda.core.commands.io_cmd

.. automodule:: happypanda.core.commands.database_cmd

.. automodule:: happypanda.core.commands.gallery_cmd

.. automodule:: happypanda.core.commands.search_cmd

.. automodule:: happypanda.core.commands.network_cmd

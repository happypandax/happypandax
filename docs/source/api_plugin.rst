Plugin API
========================================

.. automodule:: happypanda.core.plugin_interface
   :members:
   :member-order: groupwise

Commands
----------------------------------------

Besides the command entries and events listed here, HPX also provides some plugin meta events that are specific for each plugin.
These events are emitted on plugin state changes. See :class:`.PluginState` for the different kinds of plugin states.

* ``init`` -- this event is emitted for a plugin after it has initialized and *after* all its dependendencies has been initialized.
    It is therefore ideal to put the plugin's own initialization on this event.
* ``disable`` -- this event is emitted when a plugin has been disabled, either manually by the user or because of some other cause.
    The plugin should listen to this event to terminate any on-going process it has running.
* ``remove`` -- this event is emitted just before a plugin is to be removed. HPX will handle the deletion of the plugin folder.
    The ``disable`` event will always be emitted before this event. The plugin should listen to this event to remove any produced items
    that would still be lingering even after its folder has been deleted.

.. exec::

    def command_doc(module):
        import importlib
        from sphinx.util import inspect as sinspect
        from sphinx_autodoc_napoleon_typehints import process_docstring
        from sphinx.ext.napoleon import Config, docstring
        from happypanda.core import command
        import inspect
        import happypanda, collections

        mod = importlib.import_module(module)

        print(".. automodule:: {}".format(module))

        config =  Config()
        cls_str = """.. py:function:: {}{}
        {}

            **Available entries:**
        {}  

            **Available events:**
        {}

        """

        cmd_str = """.. py:function:: {}{}
        {}
        """

        cls_str = inspect.cleandoc(cls_str)
        cmd_str = inspect.cleandoc(cmd_str)

        def indent_text(txt, num=4):
            return "\n".join((num * " ") + i for i in txt)

        def doc_process(docstr, obj, retval=True, indent=4,
                            config=config, docstring=docstring,
                            inspect=inspect, process_docstring=process_docstring,
                            indent_text=indent_text):
            docstr = docstring.GoogleDocstring(inspect.cleandoc(docstr), config, obj=obj)
            docslines = str(docstr).splitlines()
            process_docstring(None, '', '', obj, config, docslines)
            if docslines:
                r = docslines.pop(0)
                # put rtype last
                if retval:
                    docslines.append(r)

            # indent
            if indent:
                docstr = indent_text(docslines, indent)
            else:
                docstr = "\n".join(docslines)
            return docstr

        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if not obj.__name__.startswith('_') and obj.__module__ == mod.__name__ and issubclass(obj, command.CoreCommand):
                if getattr(obj, 'main', False):
                    objfunc = obj.main
                else:
                    objfunc = obj.__init__

                sig = sinspect.Signature(objfunc, bound_method=True)
                obj._get_commands()
                entries = []
                events = []
                e_objfunc = None
                for x, e in sorted(obj._entries.items()):
                    esig = sinspect.Signature(objfunc)
                    esig.signature = e.signature

                    ex_local = {'happypanda': happypanda, 'collections': collections}
                    ex_local.update(mod.__dict__)
                    ex_local.update(globals())
                    exec("def e_objfunc{}:None".format(esig.signature), ex_local, ex_local)
                    e_objfunc = ex_local['e_objfunc']

                    entries.append("    - {}".format(cmd_str.format(x, esig.format_args(), str(doc_process(e.__doc__, e_objfunc, False, indent=8)))))

                for x, e in sorted(obj._events.items()):

                    esig = sinspect.Signature(objfunc)
                    esig.signature = e.signature

                    ex_local = {'happypanda': happypanda, 'collections': collections}
                    ex_local.update(mod.__dict__)
                    ex_local.update(globals())
                    exec("def e_objfunc{}:None".format(esig.signature), ex_local, ex_local)
                    e_objfunc = ex_local['e_objfunc']

                    events.append("    - {}".format(cmd_str.format(x, esig.format_args(), str(doc_process(e.__doc__, e_objfunc, False, indent=8)))))

                retval = sig.signature.return_annotation
                sig.signature = sig.signature.replace(return_annotation=inspect.Signature.empty)


                docstr = doc_process(obj.__doc__, objfunc)

                print(cls_str.format(name, sig.format_args(), str(docstr), '\n'.join(entries), '\n'.join(events)))

    command_doc("happypanda.core.commands.meta_cmd")
    command_doc("happypanda.core.commands.io_cmd")
    command_doc("happypanda.core.commands.database_cmd")
    command_doc("happypanda.core.commands.gallery_cmd")
    command_doc("happypanda.core.commands.search_cmd")
    command_doc("happypanda.core.commands.network_cmd")
    command_doc("happypanda.core.commands.download_cmd")

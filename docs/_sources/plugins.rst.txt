.. _plugins:


Writing Plugins
===============

**datacatalog-core** has a pluggable architecture to facilitate extending its
functionality. Writing a plugin consists of the following two steps:

1.  Write a class that implements one or more of the pluggable interfaces. ATOW,
    these are:

    *   searching (see :class:`~datacatalog.plugin_interfaces.AbstractSearchPlugin`)
    *   storage (see :class:`~datacatalog.plugin_interfaces.AbstractStoragePlugin`)

    It's recommended that your implementation inherits from the abstract
    interface class it implements, *but this is not required*. If your class
    implements all the methods of one or more interfaces, it is recognized
    automatically.

    The application will instantiate *one* instance of your plugin class, and
    use this instance throughout its lifetime.

2.  Add the full path of your class to the ``plugins`` section of the
    configuration file. For example, if your class lives at
    ``my.module.ElasticSearch``:

    ..  code-block:: yaml

        plugins:
          - datacatalog.default_plugins.datastore.FileStoragePlugin
          - my.module.ElasticSearch


Plugin initialization and tear-down
-----------------------------------

If your plugin needs to be initialized (eg. creating a database connection), you
have a few options. The simplest option is to do all initialization in the
constructor of your plugin class::

    class MyPlugin(object):

        def __init__(self, app):
            ...  # Initialize your plugin here

        # One or more plugin interfaces:
        ...

..  note::

    The constructor accepts a parameter ``app``, which will be the current
    :class:`application <datacatalog.application.Application`. This is optional.

The constructor is called *synchronously*, before the application's event loop
is started, so it's not trivial to call asynchronous initialization code from
here. If initializing your plugin entails some asynchronous calls (eg. because
the database connector has only an asynchronous API), the plugin can provide
asynchronous methods
:meth:`~datacatalog.plugin_interfaces.AbstractPlugin.plugin_start` and
:meth:`~datacatalog.plugin_interfaces.AbstractPlugin.plugin_stop` methods. These
will be called by the application at startup and teardown, while the event loop
is running.


Default Plugins
---------------

**datacatalog-core** comes with "batteries included": for each pluggable
interface, at least one implementation is part of the distribution. Currently,
the following implementations are provided:


FileStoragePlugin
^^^^^^^^^^^^^^^^^

Implements the :class:`~datacatalog.plugin_interfaces.AbstractStoragePlugin`
interface.

..  todo:: documentation of what it does, configuration options

See also:
    :class:`API documentation of FileStoragePlugin
    <datacatalog.default_plugins.file_storage.FileStoragePlugin>`


InMemorySearchPlugin
^^^^^^^^^^^^^^^^^^^^

Implements the :class:`~datacatalog.plugin_interfaces.AbstractSearchPlugin`
interface.

..  todo:: documentation of what it does, configuration options

See also:
    :class:`API documentation of InMemorySearchPlugin
    <datacatalog.default_plugins.in_memory_search.InMemorySearchPlugin>`

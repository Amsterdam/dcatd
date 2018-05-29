.. _sphinx_101:

Sphinx 101
==========


ReST formatting
---------------

For details on basic rST formatting, see the :ref:`sphinx:rst-primer`

*   *emphasis*, **strong empasis**, ``code``
*   *``nesting``* ``*won’t*`` ````work````
*   *roles* are formatted as ``:rolename:`some text```. RST predefines
    :emphasis:`emphasis`, :strong:`strong`, :literal:`literal`,
    :subscript:`subscript`, :superscript:`superscript`, and
    :title-reference:`title-reference`.

    #.  Numbered lists look like this

        1.  or like this, and can be nested,
        2.  as long as there is

    #.  an empty line between the lists.

*   Definition lists
        have one line for the *term*, followed by one or more indented
        multiline paragraphs.

        Like this.

*   There must be a space between the link text and the url in `hyperlinks <http://example.com/>`_.

*   Conventions for header markup:

    #. ``#`` with overline
    #. ``*`` with overline
    #. ``=``
    #. ``-``
    #. ``^``
    #. ``"``


Roles added by Sphinx
---------------------

See :doc:`sphinx:markup/inline`.

Inline markup:
    .. code-block:: rst

        :abbr:
        :command:
        :dfn:
        :file:
        :kbd:
        :mimetype:
        :program:
        :regexp:

Generic cross-referencing:
    .. code-block:: rst

        :any:
        :ref:
        :doc:
        :envvar:
        :term:
        :pep:
        :rfc:

Python cross-referencing:
    .. code-block:: rst

        :mod:
        :func:
        :data:
        :const:
        :class:
        :meth:
        :attr:
        :exc:
        :obj:

Python info field lists:
    .. code-block:: rst

        :param str sender: The person sending the message
        :param priority: The priority of the message, can be a number 1-5
        :return: the message id
        :rtype: int or None
        :raises ValueError: if the message_body exceeds 160 characters
        :raises TypeError: if the message_body is not a basestring

        :type priority: integer or None
        :type priorities: list(int)
        :type priorities: list[int]
        :type mapping: dict(str, int)
        :type mapping: dict[str, int]
        :type point: tuple(float, float)
        :type point: tuple[float, float]

    Multiple types in a type field will be linked automatically if separated by
    the word “or”.

Directives
----------

Explicit Markup Block
    begins with a line starting with ``..`` followed by whitespace and is
    terminated by the next paragraph at the same level of indentation.

Directives
    are Explicit Markup with special semantics. Directives and roles form the
    extension mechanism of rST. Basically, a directive consists of a **name**,
    **arguments**, **options** and **content**:

    .. code-block:: rst

        .. name:: arg1
                  arg2
            :option1: arg, arg
            :option2:

            Content

    Directives are defined by

    *   :ref:`Docutils <sphinx:directives>`
    *   :doc:`Sphinx <sphinx:markup/index>`, and Sphinx Extensions.


See :doc:`sphinx:domains` for ia. the **Python** and **Standard** domains with
their special directives.

See :doc:`markup/para` for documentation of many handy directives, such as:

.. code-block:: rst

    .. note::
    .. warning::
    .. versionadded:: version
    .. versionchanged:: version
    .. deprecated:: version
    .. seealso::
    .. hlist::


Google-style docstrings
-----------------------

Example::

    Args:
        path (str): The path of the file to wrap
        field_storage (FileStorage): The :class:`FileStorage` instance to wrap
        temporary (bool): Whether or not to delete the file when the File
           instance is destructed

    Returns:
        BufferedFileStorage: A buffered writable file descriptor

The following section headers are supported:

*   **Args** (alias of **Parameters**)
*   **Arguments** (alias of **Parameters**)
*   **Attributes**
*   **Example**
*   **Examples**
*   **Keyword Args** (alias of **Keyword Arguments**)
*   **Keyword Arguments**
*   **Methods**
*   **Note**
*   **Notes**
*   **Other Parameters**
*   **Parameters**
*   **Return** (alias of **Returns**)
*   **Returns**
*   **Raises**
*   **References**
*   **See Also**
*   **Todo** (doesn't work together with `sphinx.ext.todo
    <http://www.sphinx-doc.org/en/stable/ext/todo.html>`_: items won't show up
    in the ``.. todolist::``)
*   **Warning**
*   **Warnings** (alias of **Warning**)
*   **Warns**
*   **Yield** (alias of **Yields**)
*   **Yields**


Autodoc
-------

See :doc:`sphinx:ext/autodoc`.

.. code-block:: rst

    .. automodule:: my_module
        :members:
        :members: member1, member2
        :undoc-members:
        :private-members:
        :special-members:
        :synopsis: Short description
        :platform: Linux, OS-X, other platform
        :deprecated:
        :show-inheritance:
        :inherited-members:

    .. autoclass:: MyClass
    .. autoexception:: MyException
        :members:
        :members: member1, member2
        :undoc-members:
        :private-members:
        :special-members:
        :show-inheritance:
        :inherited-members:

    .. autofunction:: my_function
    .. autofunction:: my_function(arg1, arg2)
    .. automethod:: my_method
    .. automethod:: my_method(arg1, arg2)

    .. autodata::
    .. autoattribute::
        :annotation: Short description

Three ways of documenting *module data members* and *class attributes*::

    #: Single- or multi-line comment before the definition,
    #: starting with ``#:``.
    foo = "bar"  #: Single line comment *after* the definition.
    """Docstring below the definition."""


Intersphinx
-----------

Intersphinx is configured with the following mappings::

    intersphinx_mapping = {
        'python': ('https://docs.python.org/3.6/', 'python.inv'),
        'sphinx': ('http://www.sphinx-doc.org/en/stable/', 'sphinx.inv'),
        'aiohttp': ('http://aiohttp.readthedocs.io/en/stable/', 'aiohttp.inv'),
        'aiopg': ('https://aiopg.readthedocs.io/en/stable/', 'aiopg.inv'),
        'jwt': ('https://pyjwt.readthedocs.io/en/latest/', 'jwt.inv'),
    }

For each of these external packages, a full list of available reference targets
can be found in the corresponding :file:`*.inv.txt` files in the :file:`sphinx/`
directory (after the first build).

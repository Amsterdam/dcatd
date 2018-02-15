# language=rst
"""

Introduction
============


1. Streaming
------------

Out of the box, aiohttp already facilitates JSON response bodies, for example
through :func:`aiohttp.web.json_response`.  Unfortunately, aiohttp's built-in
JSON support requires that *all* the data to be serialized is held in memory,
for as long as data is being sent to the client.  When serving large datasets to
multiple clients over slow connections, this can be prohibitively resource
intensive.

This module provides a **streaming** JSON serializer, which can serialize
everything that can be serialized by :func:`json.dumps`. Additionally, it can
serialize :term:`generators <generator>` (*asynchronous* generators, to be
precise; more on that below). As a result, not all data needs to be in memory
right from the start; it can be, well, *generated* "on-the-fly", for example
while reading data from large files or large SQL-query result sets.

The :func:`encode` function will serialize a generator as a JSON *array*. So how
to produce a large JSON *object* without holding it in memory? The Python
language itself has no such thing as a *dict generator* (for reasons beyond the
scope of this document). The solution here is to use a *generator* that yields
object :const:`IM_A_DICT` as its first item, followed by zero or more key→value
pairs in the form of any 2-item :term:`iterable`, with each key being a unique
string.

Knowing all this, you might expect the following code to work::

    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃ DON'T COPY THIS EXAMPLE!!! ┃
    # ┃   instructional use only   ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    def read_lines_from_file(file):
        yield IM_A_DICT
        line_number, line = 1, file.readline()
        while len(line):
            yield tuple(str(line_number), line)
            line_number, line = line_number + 1, file.readline()

    async def my_aiohttp_handler(request):
        response = web.StreamResponse()
        ...
        for part in encode(read_lines_from_file(some_file)):
            await response.write(part)

Unfortunately, this leaves a problem to be fixed: Python's :meth:`readline
<io.TextIOBase.readline>` method is blocking, which means our whole aiohttp
server is blocked for the entire duration of the file processing.

Enter *asynchronous generators*...


2. Asynchronous Streaming
-------------------------

To solve this, function :func:`encode` is implemented as an :term:`asynchronous
generator`, and the generators you feed it must also be *asynchronous*.
(Asynchronous generators, defined in :pep:`525`, were introduced in Python
version 3.6.)

A real-world example could look like this::

    async def read_lines_from_file(file):
        yield IM_A_DICT
        line_number, line = 1, await file.readline()
        while len(line):
            yield tuple(str(line_number), line)
            line_number, line = line_number + 1, await file.readline()

    async def my_aiohttp_handler(request):
        response = web.StreamResponse()
        ...
        async for part in encode(read_lines_from_file(some_file)):
            await response.write(part)

Which could produce the following JSON body:

.. code-block:: json

    {
        "1": "Hello\\n",
        "2": "World!"
    }


3. Take home message
--------------------

If you use one of the built-in representations, you'll probably never call the
:func:`encode` function yourself.  But in order to create asynchronous,
streaming endpoints, you'll still have to know:

-   you must implement *asynchronous generators* in order to stream *JSON
    arrays*, and
-   you can produce *JSON objects* by yielding :const:`IM_A_DICT`, followed by
    ``(key, value)`` pairs.


API documentation
=================

The public interface of this module consists of:

-   :func:`encode`
-   :const:`IM_A_DICT`

----

"""

import re
import logging
import inspect
import collections
import collections.abc
import typing as T

from yarl import URL
from aiohttp import web

_logger = logging.getLogger(__name__)


IM_A_DICT = {}
# language=rst
"""First item to yield from a "dict generator".

In general, :func:`encode` serializes a generator as a JSON *array*. To produce
a JSON *object* from a generator, yield :const:`IM_A_DICT` as the first item,
followed by zero or more ``(key, value)`` pairs in the form of a 2-item
:term:`iterable`, with each key being a unique string::

    from aiohttp_extras import IM_A_DICT

This would be serialized as ``{"Hello":"world!"}``

Warning:
    Although ``IM_A_DICT`` is initialized with an empty `dict` object, it is
    essential that your generator returns the object referenced by
    ``IM_A_DICT``, and not some other random empty dictionary object.  Function
    :func:`encode` checks *object identity*, not *object value equality*.  This
    to allow a generator to produce a JSON array with an empty object as its
    first item.  That is::

        async def my_buggy_dict_generator():
            yield {}
            yield "Hello", "world!"

    would be serialized as ``[ {}, ["Hello", "world!"] ]``.

"""
_JSON_DEFAULT_CHUNK_SIZE = 1024 * 1024
_INFINITY = float('inf')

_ESCAPE = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]')
_ESCAPE_DCT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}
for i in range(0x20):
    _ESCAPE_DCT.setdefault(chr(i), '\\u{0:04x}'.format(i))


def _replace(match):
    return _ESCAPE_DCT[match.group(0)]


def _encode_string(s):
    return '"' + _ESCAPE.sub(_replace, s) + '"'


def _encode_float(o, allow_nan=False):
    # Check for specials.  Note that this type of test is processor
    # and/or platform-specific, so do tests which don't depend on the
    # internals.

    if o != o:
        text = 'NaN'
    elif o == _INFINITY:
        text = 'Infinity'
    elif o == -_INFINITY:
        text = '-Infinity'
    else:
        return repr(o)

    if not allow_nan:
        raise ValueError(
            "Out of range float values are not JSON compliant: " +
            repr(o))

    return text


async def _encode_list(obj, stack):
    if id(obj) in stack:
        raise ValueError("Cannot serialize cyclic data structure.")
    stack.add(id(obj))
    try:
        first = True
        is_dict = False
        for item in obj:
            if first:
                if item is IM_A_DICT:
                    is_dict = True
                    continue
                yield '{' if is_dict else '['
                first = False
            else:
                yield ','
            if is_dict:
                if not isinstance(item[0], str):
                    message = "Dictionary key is not a string: '%r'"
                    raise ValueError(message % item[0])
                yield _encode_string(item[0]) + ':'
                async for s in _encode(item[1], stack):
                    yield s
            else:
                async for s in _encode(item, stack):
                    yield s
        if first:
            yield '{}' if is_dict else '[]'
        else:
            yield '}' if is_dict else ']'
    finally:
        stack.remove(id(obj))


async def _encode_async_generator(obj, stack):
    if id(obj) in stack:
        raise ValueError("Cannot serialize cyclic data structure.")
    stack.add(id(obj))
    try:
        first = True
        is_dict = False
        async for item in obj:
            if first:
                if item is IM_A_DICT:
                    is_dict = True
                    continue
                yield '{' if is_dict else '['
                first = False
            else:
                yield ','
            if is_dict:
                if not isinstance(item[0], str):
                    message = "Dictionary key is not a string: '%r'"
                    raise ValueError(message % repr(item[0]))
                yield _encode_string(item[0]) + ':'
                async for s in _encode(item[1], stack):
                    yield s
            else:
                async for s in _encode(item, stack):
                    yield s
        if first:
            yield '{}' if is_dict else '[]'
        else:
            yield '}' if is_dict else ']'
    finally:
        stack.remove(id(obj))


async def _encode_dict(obj, stack):
    if id(obj) in stack:
        raise ValueError("Cannot serialize cyclic data structure.")
    stack.add(id(obj))
    try:
        first = True
        for key, value in obj.items():
            if not isinstance(key, str):
                message = "Dictionary key is not a string: '%r'"
                raise ValueError(message % repr(key))
            if first:
                yield '{' + _encode_string(key) + ':'
                first = False
            else:
                yield ',' + _encode_string(key) + ':'
            async for s in _encode(value, stack):
                yield s
        if first:
            yield '{}'
        else:
            yield '}'
    finally:
        stack.remove(id(obj))


async def _encode(obj: T.Any, stack: T.Set) -> T.Union[str, T.Any]:
    if isinstance(obj, URL):
        yield _encode_string(str(obj))
    elif hasattr(obj, 'to_dict'):
        try:
            obj = await obj.to_dict()
        except web.HTTPException as e:
            _logger.error("Unexpected exception", exc_info=e, stack_info=True)
            obj = {
                '_links': {'self': {'href': obj.canonical_rel_url}},
                '_status': e.status_code
            }
            if e.text is not None:
                obj['description'] = e.text
        async for s in _encode_dict(obj, stack):
            yield s
    elif isinstance(obj, str):
        yield _encode_string(obj)
    elif obj is None:
        yield 'null'
    elif obj is True:
        yield 'true'
    elif obj is False:
        yield 'false'
    elif isinstance(obj, float):
        yield _encode_float(obj)
    elif isinstance(obj, int):
        yield str(obj)
    elif isinstance(obj, collections.abc.Mapping):
        async for s in _encode_dict(obj, stack):
            yield s
    elif isinstance(obj, collections.abc.Iterable):
        async for s in _encode_list(obj, stack):
            yield s
    elif inspect.isasyncgen(obj):
        async for s in _encode_async_generator(obj, stack):
            yield s
    elif hasattr(obj, '__str__'):
        message = "Not sure how to serialize object of class %s:\n" \
                  "%s\nDefaulting to str()."
        _logger.warning(message, type(obj), repr(obj))
        yield _encode_string(str(obj))
    else:
        message = "Don't know how to serialize object of class %s:\n" \
                  "%s"
        _logger.error(message, type(obj), repr(obj))
        yield 'null'


async def encode(obj, chunk_size=_JSON_DEFAULT_CHUNK_SIZE) -> \
        collections.AsyncIterable:
    # language=rst
    """Asynchronous JSON serializer."""
    buffer = bytearray()
    async for b in _encode(obj, set()):
        buffer += b.encode()
        while len(buffer) >= chunk_size:
            yield buffer[:chunk_size]
            del buffer[:chunk_size]
    if len(buffer) > 0:
        yield buffer

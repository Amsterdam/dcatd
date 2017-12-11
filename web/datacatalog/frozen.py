# language=rst
"""
Recursively freeze mutable dicts, sets and lists.

Example usage::

    from .frozen import frozen

    MY_FROZEN_DICT = frozen(my_mutable_dict)

"""

import logging
from collections import abc
import types
import numbers

_logger = logging.getLogger(__name__)


def frozen(thing):
    # language=rst
    """Creates a frozen copy of ``thing``.

    :param thing:
    :type thing: bool or None or str or numbers.Number or dict or list or set
    :returns: a frozen copy of ``thing``, using the following transformations:

        -   `dict` → `types.MappingProxyType`
        -   `set` → `frozenset`
        -   `list` → `tuple`

    """
    # ¡¡¡ Ordering matters in the following if-chain !!!
    # abc.Set inherits abc.Collection, so it must be matched first.
    if (
        thing is None or
        isinstance(thing, bool) or
        isinstance(thing, numbers.Number) or
        isinstance(thing, str)
    ):
        return thing
    if isinstance(thing, abc.Mapping):
        return types.MappingProxyType({key: frozen(thing[key]) for key in thing})
    if isinstance(thing, abc.Set):
        return frozenset({frozen(value) for value in thing})
    if isinstance(thing, abc.Collection):
        return tuple([frozen(value) for value in thing])
    raise TypeError("Can't freeze object of type %s: %s" %
                    (type(thing), thing))

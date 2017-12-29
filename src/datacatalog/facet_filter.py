from enum import Enum
import typing as T


class Comparator(Enum):
    EQ = '=='
    GT = '>'
    LT = '<'
    GE = '>='
    LE = '<='
    IN = 'in'


class LogicalOperator(Enum):
    AND = 'and'
    OR = 'or'


class JSONPath(object):

    def __init__(self, path):
        self._path = path
        # TODO: more implementation

    def __lt__(self, value):
        return _FacetPremise(self._path, Comparator.LT, value)

    def __le__(self, value):
        return _FacetPremise(self._path, Comparator.LE, value)

    def __eq__(self, value):
        return _FacetPremise(self._path, Comparator.EQ, value)

    def __ne__(self, value):
        raise NotImplemented()

    def __gt__(self, value):
        return _FacetPremise(self._path, Comparator.GT, value)

    def __ge__(self, value):
        return _FacetPremise(self._path, Comparator.GE, value)

    def in_(self, value: T.Iterable):
        return _FacetPremise(self._path, Comparator.IN, value)


class Premise(object):

    def __and__(self, other):
        raise NotImplementedError()

    @property
    def premises(self) -> list:
        raise NotImplementedError()


class _FacetPremise(Premise):

    def __init__(self, path, operator, value):
        assert operator in Comparator
        self._path = path
        self._operator = operator
        self._value = value

    @property
    def premises(self):
        return [self]

    def __and__(self, other: Premise):
        if not isinstance(other, Premise):
            raise TypeError()
        return _PremiseSet(self.premises, other.premises)


class _PremiseSet(Premise):

    def __init__(self,
                 p1: T.List[_FacetPremise],
                 p2: T.List[_FacetPremise]):
        self._premises = p1 + p2

    @property
    def premises(self):
        return self._premises

    def __and__(self, other):
        return _PremiseSet(self.premises, other.premises)


class FacetFilter:
    """TODO: Documentation"""

    def __init__(self, _query):
        # language=rst
        """Build a filter, based on ``query``"""

    def filter(self, document: dict) -> bool:
        """Tests if ``document`` satisfies this filter."""

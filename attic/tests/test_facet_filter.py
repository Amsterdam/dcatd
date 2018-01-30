import pytest

from attic.src.datacatalog.facet_filter import *


def test_comparators():

    path = JSONPath('/path')
    premises = list()
    premises.append(path > 0)
    premises.append(path == 5)
    premises.append(path < 10)
    premises.append(path >= 1)
    premises.append(path <= 9)
    premises.append(path.in_(['foo', 'bar']))
    for p in premises:
        assert isinstance(p, Premise)


@pytest.mark.skip
def test_combinator():
    path = JSONPath('/path')
    premise1 = path > 0 and path < 10
    print(premise1.premises)
    assert len(premise1.premises) == 2
    premise2 = premise1 and path == 5
    assert len(premise2.premises) == 3
    premise2 = path == 5 and premise1
    assert len(premise2.premises) == 3

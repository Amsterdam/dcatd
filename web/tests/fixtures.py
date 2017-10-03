import string, random, json
from datacatalog.action_api import Facet


def random_int(max, zero_based=False):
    start = 0 if zero_based else 1
    return random.randint(start, max)


def random_string(length=None):
    if not length:
        length = random.randint(8, 16)
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase) for _ in range(length))


####
#
# For action API
#
####

def random_facets():
    """
        FACET FIELDS should contain a json-encoded list of selected facets
    """
    facets = []
    for facet in Facet:
        if random_int(1, True) == 1:
            facets.append(facet.value)
    return facets, json.dumps(facets)


def random_facet_query():
    """
        FACET QUERY should contain a collection of key-value pairs
        where the key is a facet and the value the queried value for that facet.
        keys are plaintext, values are quoted, key-value pairs are seperated by
        spaces
    """
    facet_query = {}
    for facet in Facet:
        if random_int(1, True) == 1:
            facet_query[facet.value] = random_string()
    querystring = ""
    for (k,v) in facet_query.items():
        querystring += f'{k}:"{v}" '
    return facet_query, querystring

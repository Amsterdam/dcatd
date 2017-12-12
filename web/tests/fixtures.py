import string, random, json
from datacatalog.action_api import Facet

FIXTURE_IDS = ['62513382-3b26-4bc8-9096-40b6ce8383c0',
               '17be64bb-da74-4195-9bb8-565c39846af2',
               '9c3036b8-f6ac-4a4e-9036-5a3cc90c3900']
FIXTURE_NAMES = ["100-validated-species-of-plants",
                 "1617in10-regulation-of-sale-of-overseas-properties-20170426-c",
                 "2016-regione-asia-est-oceania-classi-di-eta"]


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

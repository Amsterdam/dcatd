import time
import logging
import base64
import json
import sys

from jwcrypto.jwk import JWKSet
from jwcrypto.common import JWException

from .config import get_settings, ConfigError

_keyset = None
_keyset_last_update = 0

logger = logging.getLogger(__name__)


def get_keyset():
    global _keyset
    if not _keyset:
        init_keyset()
    return _keyset


def check_update_keyset():
    """
    When loading a JWKS from a url (public endpoint), we might need to
    check sometimes if the JWKS has changed. To avoid too many requests to
    the url, we set a minimal interval between two checks.
    """
    settings = get_settings()
    current_time = time.time()
    if current_time - _keyset_last_update >= settings['MIN_INTERVAL_KEYSET_UPDATE']:
        init_keyset()


def init_keyset():
    """
    Initialize keyset, by loading keyset from settings and/or from url
    """
    global _keyset, _keyset_last_update

    _keyset = JWKSet()
    _keyset_last_update = time.time()
    settings = get_settings()

    if settings.get('jwks'):
        load_jwks(settings['jwks'])

    if settings.get('jwks_url'):
        load_jwks_from_url(settings['jwks_url'])

    if len(_keyset['keys']) == 0:
        raise ConfigError('No keys loaded!')


def load_jwks(jwks):
    global _keyset
    try:
        _keyset.import_keyset(jwks)
    except JWException as e:
        raise ConfigError("Failed to import keyset from settings") from e
    logger.info('Loaded JWKS from JWKS setting.')


def load_jwks_from_url(jwks_url):
    global _keyset
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConfigError(
            "Failed to get Keycloak keyset from url: {}, error: {}".format(jwks_url, e)
        )
    try:
        _keyset.import_keyset(response.text)
    except JWException as e:
        raise ConfigError("Failed to import Keycloak keyset") from e
    logger.info('Loaded JWKS from JWKS_URL setting {}'.format(jwks_url))


__all__ = dir(sys.modules[__name__])

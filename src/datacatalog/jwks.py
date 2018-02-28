import base64
import collections
import json
from types import MappingProxyType

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.utils import int_from_bytes

_Key = collections.namedtuple('Key', 'alg key')
"""Immutable type for key storage"""

_KeySet = collections.namedtuple('KeySet', 'signers verifiers')
"""Immutable type for key sets"""


class JWKError(Exception):
    """Error raised when parsing a JWKSet fails."""


def load(jwks):
    """Parse a JWKSet and return a dictionary that maps key IDs on keys."""
    sign_keys = {}
    verify_keys = {}
    try:
        keyset = json.loads(jwks)
        for key in keyset['keys']:
            for op in key['key_ops']:
                if op == 'sign':
                    k = sign_keys
                elif op == 'verify':
                    k = verify_keys
                else:
                    raise JWKError("Unsupported key operation: {}".format(op))
                if key['kty'] == 'oct':
                    k[key['kid']] = _Key(alg=key['alg'], key=base64.urlsafe_b64decode(key['k']))
                elif key['kty'] == 'EC':
                    alg, ec_key = _load_ecdsa(key, op == 'verify')
                    k[key['kid']] = _Key(alg=alg, key=ec_key)
                else:
                    raise JWKError("Unsupported key type: {}".format(key['kty']))
    except (KeyError, json.JSONDecodeError) as e:
        raise JWKError() from e
    keys = _KeySet(signers=MappingProxyType(sign_keys), verifiers=MappingProxyType(verify_keys))
    return keys


def _load_ecdsa(key, is_verifier):
    if key.get('kty') != 'EC':
        raise JWKError('Not an Elliptic curve key')

    if 'x' not in key or 'y' not in key:
        raise JWKError('Not an Elliptic curve key')

    x = base64.urlsafe_b64decode(key.get('x'))
    y = base64.urlsafe_b64decode(key.get('y'))

    curve = key.get('crv')
    if curve == 'P-256':
        if len(x) == len(y) == 32:
            alg = 'ES256'
            curve_obj = ec.SECP256R1()
        else:
            raise JWKError("Coords should be 32 bytes for curve P-256")
    elif curve == 'P-384':
        if len(x) == len(y) == 48:
            alg = "ES384"
            curve_obj = ec.SECP384R1()
        else:
            raise JWKError("Coords should be 48 bytes for curve P-384")
    elif curve == 'P-521':
        if len(x) == len(y) == 66:
            alg = "ES512"
            curve_obj = ec.SECP521R1()
        else:
            raise JWKError("Coords should be 66 bytes for curve P-521")
    else:
        raise JWKError("Invalid curve: {}".format(curve))

    public_numbers = ec.EllipticCurvePublicNumbers(
        x=int_from_bytes(x, 'big'), y=int_from_bytes(y, 'big'), curve=curve_obj
    )

    if not is_verifier:
        if 'd' not in key:
            raise JWKError("Signing ECDSA keys must contain private key")
        d = base64.urlsafe_b64decode(key.get('d'))
        if len(d) != len(x):
            raise JWKError(
                "D should be {} bytes for curve {}", len(x), curve
            )

        key = ec.EllipticCurvePrivateNumbers(
            int_from_bytes(d, 'big'), public_numbers
        ).private_key(default_backend())
    else:
        key = public_numbers.public_key(default_backend())

    return alg, key

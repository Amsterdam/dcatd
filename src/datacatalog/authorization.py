import logging
import re
import json
import typing as T
import urllib.parse

from aiohttp import web

from jwcrypto.jwt import JWT, JWTExpired, JWTMissingKey
from jwcrypto.jws import InvalidJWSSignature

from .config import get_settings
from .jwks import get_keyset, check_update_keyset

_logger = logging.getLogger(__name__)

LOCAL_ALWAYS_OK = False


async def _extract_scopes(request: web.Request) -> T.Set:
    if LOCAL_ALWAYS_OK and request.url.host == 'localhost':
        scopes = {'CAT/W', 'CAT/R'}
        subject = 'test@test.nl'
    else:
        authorization_header = request.headers.get('authorization')
        if authorization_header is None:
            return set()
        match = re.fullmatch(r'bearer ([-\w.=]+)', authorization_header, flags=re.IGNORECASE)
        if not match:
            return set()

        raw_jwt = match[1]
        try:
            jwt = decode_token(raw_jwt)
        except JWTExpired:
            _logger.info(
                'Auth problem: token expired'
            )
            return set()
        except JWTMissingKey:
            check_update_keyset()
            try:
                jwt = decode_token(raw_jwt)
            except JWTMissingKey as e:
                _logger.warning('API authz problem: unknown key. {}'.format(e))
                raise web.HTTPBadRequest(text="Unknown key identifier: {}".format(header['kid'])) from None

        claims = get_claims(jwt)
        subject = claims['sub']
        scopes = claims['scopes']

    request.authz_scopes = scopes
    request.authz_subject = subject
    return scopes


def decode_token(raw_jwt):
    settings = get_settings()
    try:
        jwt = JWT(jwt=raw_jwt, key=get_keyset(), algs=settings['allowed_signing_algorithms'])
    except InvalidJWSSignature as e:
        _logger.warning('Auth problem: invalid signature. {}'.format(e))
        raise web.HTTPBadRequest(text='Invalid Bearer token')
    except ValueError as e:
        _logger.warning(
            'Auth problem: {}'.format(e))
        raise web.HTTPBadRequest(text='Invalid Bearer token')
    return jwt


def get_claims(jwt):
    claims = json.loads(jwt.claims)
    if 'scopes' in claims:
        # Authz token structure
        return {
            'sub': claims.get('sub'),
            'scopes': set(claims['scopes'])
        }
    elif claims.get('realm_access'):
        # Keycloak token structure
        return {
            'sub': claims.get('sub'),
            'scopes': {convert_scope(r) for r in claims['realm_access']['roles']}
        }
    raise web.HTTPBadRequest(text='No scopes in access token')


def convert_scope(scope):
    """ Convert Keycloak role to authz style scope
    """
    return scope.upper().replace("_", "/")


async def _extract_api_key_info(request: web.Request,
                                security_scheme: T.Dict) -> T.Any:
    assert security_scheme['in'] == 'header'
    assert security_scheme['name'] == 'Authorization'
    authorization_header = request.headers.get('authorization')
    if authorization_header is None:
        return False
    match = re.fullmatch(r'apikey ([-\w]+=*)', authorization_header)
    if not match:
        return False
    return match[1] == request.app['config']['authz_admin']['api_key']


async def _extract_authz_info(request: web.Request,
                              security_definitions: T.Dict[str, T.Dict[str, T.Any]]):
    result = {}
    for key, security_scheme in security_definitions.items():
        security_type = security_scheme['type']
        if security_type == 'oauth2':
            result[key] = await _extract_scopes(request)
        elif security_type == 'apiKey':
            result[key] = await _extract_api_key_info(request, security_scheme)
        else:
            _logger.error('Unknown security type: %s' % security_type)
            raise web.HTTPInternalServerError()
    return result


async def middleware(app, handler):
    openapi = app['openapi']
    baseurl = app.config['web']['baseurl']
    base_path = urllib.parse.urlparse(baseurl).path
    path_offset = len(base_path)
    if path_offset > 0 and base_path[-1] == '/':
        path_offset -= 1
    paths = openapi['paths']

    async def middleware_handler(request: web.Request) -> web.Response:
        req_path = request.rel_url.raw_path[path_offset:]
        method = request.method
        path, pathspec = _get_path_spec(paths, req_path, method.lower())

        if path is not None and 'security' in pathspec:
            await _enforce_one_of(request, pathspec['security'])

        return await handler(request)
    return middleware_handler


async def _enforce_one_of(request: web.Request,
                          security_requirements: T.List[
                              T.Optional[T.Dict[
                                str, T.Optional[T.Iterable]
                              ]]
                          ]):
    for security_requirement in security_requirements:
        if await _enforce_all_of(request, security_requirement):
            return
    raise web.HTTPUnauthorized()


async def _enforce_all_of(request: web.Request,
                          security_requirements: T.Optional[T.Dict[
                              str, T.Optional[T.Iterable]
                          ]]) -> bool:
    if security_requirements is None:
        return True
    openapi = request.app['openapi']
    security_definitions = openapi['components']['securitySchemes']
    all_authz_info = await _extract_authz_info(request, security_definitions)

    for requirement, scopes in security_requirements.items():
        authz_info = all_authz_info[requirement]
        security_type = security_definitions[requirement]['type']
        if security_type == 'oauth2':
            if len(set(scopes) - authz_info) > 0:
                _logger.debug("Request with insufficient scopes")
                return False
        elif security_type == 'apiKey':
            if not authz_info:
                return False
        else:
            _logger.error('Unexpected security type: %s' % security_type)
            raise web.HTTPInternalServerError()
    _logger.debug("Request with sufficient authorization")
    return True


def _get_path_spec(paths: dict, path: str, method: str=None) -> T.Optional[T.Tuple[str, str]]:
    """Adapted from swagger-parser library."""
    # Get the specification of the given path
    path_spec = None
    path_name = None
    if path in paths:
        path_spec = paths[path]
        path_name = path
    else:
        for base_path in paths.keys():
            regex_from_path = re.compile(re.sub('{[^/]*}', '([^/]*)', base_path))
            if re.fullmatch(regex_from_path, path):
                path_spec = paths[base_path]
                path_name = base_path

    # Test method if given
    if path_spec is not None and method is not None and method in path_spec.keys():
        path_spec = path_spec[method]

    return path_name, path_spec

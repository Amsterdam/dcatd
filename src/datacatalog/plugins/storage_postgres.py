from pkg_resources import resource_stream
import secrets
import typing as T
import yaml

import aiopluggy

hookimpl = aiopluggy.HookimplMarker('datacatalog')


@hookimpl
def initialize(app) -> T.Optional[T.Coroutine]:
    # language=rst
    """ Initialize the plugin.

    This function validates the configuration and creates a database engine.

    """
    with resource_stream(__name__, 'storage_postgres_config_schema.yml') as s:
        schema = yaml.load(s)
    app.config.validate(schema)
    dbconf = app.config['postgres_storage_plugin']
    _logger.info("Connecting to database: postgres://%s:%i/%s",
                 dbconf['host'], dbconf['port'], dbconf['dbname'])
    engine_context = aiopg.sa.create_engine(
        user=dbconf['user'],
        database=dbconf['dbname'],
        host=dbconf['host'],
        port=dbconf['port'],
        password=dbconf['password'],
        client_encoding='utf8'
    )
    app['engine'] = await engine_context.__aenter__()
    await initialize_database(app['engine'], required_accounts=app['config']['authz_admin']['required_accounts'])

    async def on_shutdown(app):
        await engine_context.__aexit__(None, None, None)
    app.on_shutdown.append(on_shutdown)


@hookimpl
def storage_retrieve(id: str) -> dict:
    # language=rst
    """ Get document by id.

    :returns: a "JSON dictionary"
    :raises KeyError: if not found

    """


@hookimpl
def storage_retrieve_ids() -> T.Generator[int]:
    # language=rst
    """ Get a list containing all document identifiers.
    """


@hookimpl
def storage_store(id: str, doc: dict, etag: T.Optional[str]) -> str:
    # language=rst
    """ Store document.

    :param id: the ID under which to store this document. May or may not
        already exist in the data store.
    :param doc: the document to store; a "JSON dictionary".
    :param etag: the last known ETag of this document, or ``None`` if no
        document with this ``id`` should exist yet.
    :returns: new ETag
    :raises:

    """


@hookimpl
def storage_id() -> str:
    # language=rst
    """New unique identifier.

    Returns a URL-safe random token with 80 bits of entropy, base64 encoded in
    ~13 characters. Given the birthday paradox this should be safe upto about
    10 bilion (2^35) entries, when the probability of collisions is
    approximately 0.05% (p=0.0005).

    """
    return secrets.token_urlsafe(nbytes=10)

from aiohttp.test_utils import make_mocked_coro

async def test_index(dcat_client):
    resp = await dcat_client.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert 'Hello, World' in text


async def test_health_ok(dcat_client):
    resp = await dcat_client.get('/system/health')
    assert resp.status == 200
    text = await resp.text()
    assert 'systemhealth is OK' in text


async def test_health_not_ok_datastore(dcat_client, monkeypatch):
    monkeypatch.setattr(
        'datacatalog.plugins.file_storage.plugin._health_check',
        make_mocked_coro('Oops')
    )
    resp = await dcat_client.get('/system/health')
    assert resp.status == 503


async def test_health_not_ok_search(dcat_client, monkeypatch):
    async def is_healthy(_):
        return False
    monkeypatch.setattr(
        'datacatalog.plugins.in_memory_search.plugin._health_check',
        make_mocked_coro('Oops')
    )
    resp = await dcat_client.get('/system/health')
    assert resp.status == 503

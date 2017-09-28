from datacatalog.app import app

async def test_hello(test_client, loop):
    client = await test_client(app)

    resp = await client.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert 'Hello, World' in text

    resp = await client.get('/system/health')
    assert resp.status == 200
    text = await resp.text()
    assert 'systemhealth is OK' in text

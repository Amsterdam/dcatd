import json


async def test_show(dcat_client, package):
    resp = await dcat_client.get(f'/datacatalog/api/3/action/package_show?id={package.id}')
    assert resp.status == 200
    text = await resp.text()
    assert package.id in text


async def test_show_by_name(dcat_client, package, all_packages):
    resp = await dcat_client.get(f'/datacatalog/api/3/action/package_show?id={package.name}')
    assert resp.status == 200
    text = await resp.text()
    json_object = json.loads(text)
    assert json_object['result']['id'] == package.id


async def test_show_no_id(dcat_client):
    resp = await dcat_client.get(f'/datacatalog/api/3/action/package_show')
    assert resp.status == 400


async def test_search(dcat_client, all_packages):
    resp = await dcat_client.get('/datacatalog/api/3/action/package_search')
    assert resp.status == 200
    text = await resp.text()
    for package in all_packages:
        assert package.id in text


async def test_list(dcat_client, all_packages):
    resp = await dcat_client.get('/datacatalog/api/3/action/package_list')
    assert resp.status == 200
    text = await resp.text()
    for package in all_packages:
        assert package.name in text


async def test_non_existent_action(dcat_client, random_string):
    non_existent = random_string
    resp = await dcat_client.get(f'/datacatalog/api/3/action/{non_existent}')
    assert resp.status == 404

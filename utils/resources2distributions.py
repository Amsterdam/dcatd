import aiohttp
import asyncio
import collections
import glob
import json
import os
import sys
import uvloop

uploadurl = 'https://acc.api.data.amsterdam.nl/dcatd/files'


def _ckan_url(url):
    return 'https://api.data.amsterdam.nl/catalogus/dataset' in url and 'resource' in url


def _distributions():
    distributions = collections.defaultdict(list)
    for f in glob.iglob('dcatdata/*.json'):
        with open(f) as reader:
            doc = json.loads(reader.read())
        docdists = doc.get('dcat:distribution', [])
        if type(docdists) is not list:
            docdists = [docdists]
        for distribution in docdists:
            url = distribution['dcat:accessURL']
            if _ckan_url(url):
                distributions[doc['dct:identifier']].append({
                    'url': url,
                    'mime': distribution['dct:format'],
                    'name': os.path.basename(url)
                })
    return distributions


async def _download(alldistributions):
    try:
        os.mkdir('dists', mode=0o770)
    except FileExistsError:
        pass

    async with aiohttp.ClientSession() as session:

        print('Downloading: ', end='')

        async def download_distribution(dataset, url, name):
            try:
                async with session.get(url) as resp:
                    with open(os.path.join('dists', dataset, name), 'wb') as fd:
                        while True:
                            chunk = await resp.content.read(1024)
                            if not chunk:
                                break
                            fd.write(chunk)
            except aiohttp.InvalidURL:
                print('X', end='')
            else:
                print('.', end='')

        for dataset, distributions in alldistributions.items():
            try:
                os.mkdir('dists/{}'.format(dataset), mode=0o770)
            except FileExistsError:
                pass
            await asyncio.gather(*[
                download_distribution(
                    dataset, distribution['url'], distribution['name']
                )
                for distribution in distributions
            ])
        print(' DONE')


async def _upload(alldistributions, token):
    results = {}

    async with aiohttp.ClientSession() as session:

        print('Uploading: ', end='')

        async def upload_distribution(dataset, oldurl, name, mime):
            data = aiohttp.FormData()
            data.add_field('distribution',
                           open(os.path.join('dists', dataset, name), 'rb'),
                           filename=name,
                           content_type=mime)
            response = await session.post(
                uploadurl, data=data, headers={'Authorization': 'Bearer {}'.format(token)}
            )
            results[dataset][oldurl] = response.headers['Location']
            print('.', end='')

        for dataset, distributions in alldistributions.items():
            results[dataset] = {}
            await asyncio.gather(*[
                upload_distribution(
                    dataset, distribution['url'],
                    distribution['name'], distribution['mime']
                )
                for distribution in distributions
            ])

        print(' DONE')

    return results


def _update_distributions(urls):
    for f in glob.iglob('dcatdata/*.json'):
        with open(f) as reader:
            doc = json.loads(reader.read())
        dataset = doc['dct:identifier']
        if dataset not in urls:
            continue
        docdists = doc['dcat:distribution']
        if type(docdists) is list:
            for distribution in docdists:
                url = distribution['dcat:accessURL']
                if url in urls[dataset]:
                    distribution['dcat:accessURL'] = urls[dataset][url]
        else:
            url = docdists['dcat:accessURL']
            if url in urls[dataset]:
                docdists['dcat:accessURL'] = urls[dataset][url]
        with open(f, 'w+') as writer:
            writer.write(json.dumps(doc, indent='    '))


if __name__ == '__main__':
    token = os.getenv('TOKEN')
    if token is None:
        print('set TOKEN in env')
        exit(1)
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    alldists = _distributions()
    loop.run_until_complete(_download(alldists))
    urls = loop.run_until_complete(_upload(alldists, token))
    _update_distributions(urls)

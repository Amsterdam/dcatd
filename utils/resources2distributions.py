import aiohttp
import argparse
import asyncio
import collections
import glob
import json
import os
import sys
import uvloop


def _ckan_url(url):
    return 'https://api.data.amsterdam.nl/catalogus/dataset' in url and 'resource' in url


def _distributions():
    distributions = collections.defaultdict(list)
    for f in glob.iglob('dcatdata/*.json'):
        with open(f) as reader:
            doc = json.loads(reader.read())
        docdists = doc.get('dcat:distribution', [])
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

        print('Downloading: ', end='', flush=True)

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
                print('X', end='', flush=True)
            else:
                print('.', end='', flush=True)

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
        print(' DONE', flush=True)


async def _upload(alldistributions, token, uploadurl):
    results = {}

    async with aiohttp.ClientSession() as session:

        print('Uploading: ', end='', flush=True)

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
            print('.', end='', flush=True)

        for dataset, distributions in alldistributions.items():
            results[dataset] = {}
            await asyncio.gather(*[
                upload_distribution(
                    dataset, distribution['url'],
                    distribution['name'], distribution['mime']
                )
                for distribution in distributions
            ])

        print(' DONE', flush=True)

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


parser = argparse.ArgumentParser(description='CKAN 2 DCAT.')
parser.add_argument('uploadurl', metavar='URL', help='dcatd /files endpoint to use')
parser.add_argument('token', metavar='JWT', help='token to use for upload')

if __name__ == '__main__':
    args = parser.parse_args()
    token = args.token
    uploadurl = args.uploadurl
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    alldists = _distributions()
    loop.run_until_complete(_download(alldists))
    urls = loop.run_until_complete(_upload(alldists, token, uploadurl))
    _update_distributions(urls)

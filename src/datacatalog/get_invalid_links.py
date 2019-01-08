import re

import aiohttp
import asyncio
import asyncpg
import argparse
import os
import json
import time
from urllib.parse import urljoin

from datacatalog.plugins.postgres import _etag_from_str

MAX_REQUESTS = 10
MAX_REDIRECTS = 5


def write(msg):
    print(msg, flush=True)


async def storage_all(con):
    # language=rst
    _Q = '''SELECT id, doc->>'dct:title' as title, doc FROM dataset'''
    async with con.transaction():
        stmt = await con.prepare(_Q)
        async for row in stmt.cursor():
            yield row['id'], row['title'], json.loads(row['doc'])


async def update_doc(con, id, doc):
    _Q_UPDATE_DOC = 'UPDATE "dataset" SET doc=$1, etag=$2 WHERE id=$3 RETURNING id'
    new_doc = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    new_etag = _etag_from_str(new_doc)
    async with con.transaction():
        await con.execute(_Q_UPDATE_DOC, new_doc, new_etag, id);
    return new_etag


async def check_link(id: str, r_id: str, title: str, r_title: str, url: str):
    async with aiohttp.ClientSession() as session:

        try:
            redirects = 0
            done = False
            while not done:
                async with session.head(url, allow_redirects=False) as resp:
                    if resp.status in (301, 302, 303, 307, 308):
                        redirects += 1
                        if redirects > MAX_REDIRECTS:
                            raise Exception("Too many redirections")
                        r_url = resp.headers.get("Location")
                        # The OIS website does return in the Location header only the domain name and
                        # not the path for a https redirect. Therefore we append the path ourselves again
                        if url.startswith('http://'):
                            https_url = 'https://' + url[7:]
                            if len(r_url) < len(https_url) and https_url.startswith(r_url):
                                r_url = https_url
                        if not re.match('^http(?:s)?://', r_url):
                            r_url = urljoin(url, r_url)
                        url = r_url
                        continue
                    status = resp.status
                    message = resp.reason
                    done = True

        except Exception as exc:
            status = 400
            message = str(exc)
        message = f"{status}|{id}|{r_id}|{title}|{r_title}|{url}|{message}"
        return (status, message)


async def do_work(make_unavailable, show_unavailable):
    now = time.strftime("%c")
    write(f"Ongeldige URL links in datacatalogus per {now}\n\n")
    dbname = os.getenv('DB_DATABASE', 'dcatd')
    dbhost = os.getenv('DB_HOST', 'localhost')
    dbpass = os.getenv('DB_PASS', 'dcatd')
    dbport = os.getenv('DB_PORT', 5433)
    dbuser = os.getenv('DB_USER', 'dcatd')

    conn = await asyncpg.connect(user=dbuser, password=dbpass,
                                 database=dbname, host=dbhost, port=dbport)

    iterator = storage_all(conn)
    total_count = 0
    total_beschikbaar_count = 0
    invalid_count = 0
    invalid_beschikbaar_count = 0

    checks = []

    dataset_links = {}
    async for docid, title, doc in iterator:
        title = doc.get('dct:title', '')
        ams_status = doc.get('ams:status', 'beschikbaar')
        dataset_links[docid] = { 'total_links' : 0, 'invalid_links' : 0, 'ams:status' : ams_status}
        for distribution in doc.get('dcat:distribution', []):
            dataset_links[docid]['total_links'] += 1
            total_count += 1
            if ams_status == 'beschikbaar':
                total_beschikbaar_count += 1
            id = distribution['dc:identifier']
            url = distribution.get('dcat:accessURL')
            r_title = distribution.get('dct:title', '')
            checks.append((docid, id, title, r_title, url))

    for i in range(0, len(checks), MAX_REQUESTS):
        tasks = []
        for check in checks[i:i + MAX_REQUESTS]:
            tasks.append(check_link(*check))
        result = await asyncio.gather(*tasks)
        for r in result:
            if r[0] >= 400:
                doc_id = r[1].split('|')[1]
                dataset_links[doc_id]['invalid_links'] += 1
                invalid_count += 1
                ams_status = dataset_links[doc_id]['ams:status']
                if ams_status == 'beschikbaar':
                    invalid_beschikbaar_count += 1
                    write(ams_status + '|' + r[1])
                elif show_unavailable:
                    write(ams_status + '|' + r[1])

    unavailable_count = 0
    if make_unavailable:
        iterator = storage_all(conn)
        async for docid, title, doc in iterator:
            if dataset_links[docid]['invalid_links'] > 0 and doc['ams:status'] == 'beschikbaar':
                doc['ams:status'] = 'niet_beschikbaar'
                await update_doc(conn, docid, doc)
                unavailable_count += 1
                write(f"Make dataset {docid} unavailable : {dataset_links[docid]['invalid_links']} invalid links from {dataset_links[docid]['total_links']}")

    perc_beschikbaar = invalid_beschikbaar_count * 100 / total_beschikbaar_count if total_beschikbaar_count > 0 else 0
    write(f"\nTotal available number of links   :  {total_beschikbaar_count}")
    write(f"Invalid available number of links :  {invalid_beschikbaar_count}")
    write(f"\nPercentage invalid URLS {perc_beschikbaar:.2f}")

    perc = invalid_count * 100 / total_count
    write(f"\nTotal number of links   :  {total_count}")
    write(f"Invalid number of links :  {invalid_count}")
    write(f"\nPercentage invalid URLS {perc:.2f}")
    write(f"\nDatasets made unavailable because of invalid links : {unavailable_count}")
    await conn.close()


def get_invalid_links():
    parser = argparse.ArgumentParser()
    parser.add_argument("--make_unavailable", choices=['yes', 'no'], default='no', help="Maak dataset 'Niet beschikbaar' indien er een ongeldig link is")
    parser.add_argument("--show_unavailable", choices=['yes', 'no'], default='no', help="Toon niet beschikbare, ongeldig links")

    args = parser.parse_args()

    start = time.time()
    loop = asyncio.get_event_loop()

    loop.run_until_complete(do_work(args.make_unavailable == 'yes', args.show_unavailable == 'yes'))
    loop.close()

    end = time.time()
    print("\nTotal time: {}".format(end - start))

    return 0


if __name__ == '__main__':
    get_invalid_links()

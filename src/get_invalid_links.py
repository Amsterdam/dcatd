import aiohttp
import asyncio
import asyncpg
import os
import json
import time

MAX_REQUESTS = 10
MAX_REDIRECTS = 5

async def on_request_start(
        session, trace_config_ctx, params):
    print("Starting request")

async def on_request_end(session, trace_config_ctx, params):
    print("Ending request")


def write(msg):
    print(msg, flush=True)


async def storage_all(con):
    # language=rst
    _Q = '''SELECT id, doc->>'dct:title' as title, doc FROM dataset'''
    async with con.transaction():
        stmt = await con.prepare(_Q)
        async for row in stmt.cursor():
            yield row['id'], row['title'], json.loads(row['doc'])


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
                        url = r_url
                        continue
                    status = resp.status
                    message = resp.reason
                    done = True

        except Exception as exc:
            status = 400
            message = str(exc)
        message = f"{status} : ({id},{r_id}): {title},{r_title} : {url}: {message}"
        return (status, message)


async def do_work():
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
    invalid_count = 0

    checks = []
    async for docid, title, doc in iterator:
        title = doc.get('dct:title', '')
        for distribution in doc.get('dcat:distribution', []):
            total_count += 1
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
                invalid_count += 1
                write(r[1])
    perc = invalid_count * 100 / total_count
    write(f"\nPercentage invalid URLS {perc:.2f}")
    await conn.close()


def main():
    start = time.time()
    loop = asyncio.get_event_loop()

    loop.run_until_complete(do_work())
    loop.close()

    end = time.time()
    print("\nTotal time: {}".format(end - start))

    return 0


if __name__ == '__main__':
    main()

import argparse

from aiohttp import web

from . import application


def main() -> int:
    parser = argparse.ArgumentParser(prog='dcatd')
    parser.add_argument('--config', '-c', dest='accumulate', action='store_const',
                        const=sum, default=max,
                        help='sum the integers (default: find the max)')
    aio_app = application.Application()
    web.run_app(aio_app, port=aio_app.config['web']['port'])
    return 0


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""See <https://setuptools.readthedocs.io/en/latest/>.
"""
from setuptools import setup, find_packages

setup(


    # ┏━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃ Publication Metadata ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━┛
    version='1.1.0',
    name='datacatalog-core',
    description="Core of the Amsterdam Data Catalog Project",
    # TODO:
    # long_description="""
    #
    # """,
    url='https://github.com/Amsterdam/datacatalog-core',
    author='Amsterdam Data en Informatie',
    author_email='datapunt@amsterdam.nl',
    license='Mozilla Public License Version 2.0',
    classifiers=[
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': [
            'datacatalog-core=datacatalog.main:main',
            'aschema-sync=dcatsync.sync_aschema:main'
        ]
    },


    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃ Packages and package data ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    package_dir={'': 'src'},
    packages=find_packages('src'),

    # TODO: is there a more elegant way to do this?
    package_data={
        'datacatalog': ['*.yml'],
        'datacatalog.handlers': ['*.yml'],
        'datacatalog.plugins': ['*.yml'],
        'datacatalog.plugins.postgres': ['*.yml'],
        'datacatalog.plugins.swift': ['*.yml'],
    },


    # ┏━━━━━━━━━━━━━━┓
    # ┃ Requirements ┃
    # ┗━━━━━━━━━━━━━━┛
    python_requires='~=3.5',
    setup_requires=[
        'pytest-runner'
    ],
    install_requires=[
        'aiohttp',
        'aiohttp_cors',
        'aiopluggy',
        'amsterdam-schema',
        'asyncpg',  # for postgres plugin
        'bleach',  # Markdown to text conversion
        'cryptography',
        'datapunt_config_loader',
        'jsonschema',
        'jsonpointer',
        'pluggy',
        'jwcrypto',
        'pyjwt',
        'pyld',
        'PyYaml',
        'sentry-sdk',
        'whoosh',
        'requests',

        # Recommended by aiohttp docs:
        'aiodns',    # optional asynchronous DNS client
        'uvloop',    # optional fast eventloop for asyncio
        'xlrd',
        'deepdiff',
    ],
    extras_require={
        'docs': [
            # 'MacFSEvents',  # Too Mac-specific?
            'Sphinx',
            'sphinx-autobuild',
            'sphinx-autodoc-typehints',
            'sphinx-rtd-theme',
        ],
        'dev': [
            'aiohttp-devtools'
        ],
        'test': [
            'mockito',
            'pytest',
            'pytest-cov',
            'pytest-aiohttp',
        ],
    },
    # To keep PyCharm from complaining about missing requirements:
    tests_require=[
        'mockito',
        'pytest',
        'pytest-cov',
        'pytest-aiohttp',
        'pytest-mock',
        'attrdict',
    ],
)

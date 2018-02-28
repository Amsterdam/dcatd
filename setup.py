#!/usr/bin/env python
"""See <https://setuptools.readthedocs.io/en/latest/>.
"""
from setuptools import setup, find_packages

setup(


    # ┏━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃ Publication Metadata ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━┛
    version='1.0.0',
    name='datacatalog-core',
    description="Core of the Amsterdam Data Catalog Project",
    # TODO:
    # long_description="""
    #
    # """,
    url='https://github.com/Amsterdam/datacatalog-core',
    author='Amsterdam City Data',
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
            'datacatalog-core=datacatalog.main:main'
        ]
    },


    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃ Packages and package data ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    package_dir={'': 'src'},
    packages=find_packages('src'),
    package_data={
        'datacatalog': ['*.yml'],
        'datacatalog.handlers': ['*.yml'],
        'datacatalog.plugins': ['*.yml'],
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
        'aiopluggy',
        'bleach',
        'datapunt_config_loader',
        'jsonschema',
        'jsonpointer',
        'pluggy',
        'pyjwt',
        'pyld',
        'PyYaml',
        'whoosh',

        # for postgres storage plugin
        'asyncpg', # postgres plugin

        # Recommended by aiohttp docs:
        'aiodns',    # optional asynchronous DNS client
        'uvloop',    # optional fast eventloop for asyncio
    ],
    extras_require={
        'docs': [
            # 'MacFSEvents',  # Too Mac-specific?
            'Sphinx',
            'sphinx-autobuild',
            'sphinx-autodoc-typehints',
            'sphinx_rtd_theme',
        ],
        'dev': [
            'aiohttp-devtools'
        ],
        'test': [
            'pytest',
            'pytest-cov',
            'pytest-aiohttp',
        ],
    },
    # To keep PyCharm from complaining about missing requirements:
    tests_require=[
        'pytest',
        'pytest-aiohttp',
    ],
)

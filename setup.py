#!/usr/bin/env python
"""See <https://setuptools.readthedocs.io/en/latest/>.
"""
from setuptools import setup, find_packages

setup(
    # ┏━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃ Publication Metadata ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━┛
    version="1.1.0",
    name="datacatalog-core",
    description="Core of the Amsterdam Data Catalog Project",
    # TODO:
    # long_description="""
    #
    # """,
    url="https://github.com/Amsterdam/datacatalog-core",
    author="Amsterdam Data en Informatie",
    author_email="datapunt@amsterdam.nl",
    license="Mozilla Public License Version 2.0",
    classifiers=[
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points={
        "console_scripts": [
            "datacatalog-core=datacatalog.main:main",
        ]
    },
    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃ Packages and package data ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    package_dir={"": "src"},
    packages=find_packages("src"),
    # TODO: is there a more elegant way to do this?
    package_data={
        "datacatalog": ["*.yml"],
        "datacatalog.handlers": ["*.yml"],
        "datacatalog.plugins": ["*.yml"],
        "datacatalog.plugins.postgres": ["*.yml"],
        "datacatalog.plugins.swift": ["*.yml"],
    },
    # ┏━━━━━━━━━━━━━━┓
    # ┃ Requirements ┃
    # ┗━━━━━━━━━━━━━━┛
    python_requires="~=3.7",
    setup_requires=["pytest-runner"],
    install_requires=[
        "aiohttp==3.9.2",
        "aiohttp_cors==0.7.0",
        "aiopluggy==0.1.5rc3",
        "amsterdam-schema==0.1.2",
        "asyncpg==0.26.0",  # for postgres plugin
        "bleach==3.3.0",  # Markdown to text conversion
        "cryptography==42.0.4",
        "datapunt_config_loader==1.1.2",
        "jsonschema==3.2.0",
        "jsonpointer==2.0",
        "pluggy==0.13.1",
        "jwcrypto==1.5.1",
        "pyld==1.0.5",
        "PyYaml==5.4",
        "sentry-sdk==1.14.0",
        "whoosh==2.7.4",
        "requests==2.31.0",
        "urllib3==1.26.18",
        # Recommended by aiohttp docs:
        "aiodns==2.0.0",  # optional asynchronous DNS client
        "uvloop==0.17.0",  # optional fast eventloop for asyncio
        "click==7.1.2",
    ],
    extras_require={
        "docs": [
            # 'MacFSEvents',  # Too Mac-specific?
            "Sphinx==3.0.3",
            "sphinx-autobuild==0.7.1",
            "sphinx-autodoc-typehints==1.10.3",
            "sphinx-rtd-theme==0.4.3",
        ],
        "dev": ["aiohttp-devtools==0.13.1"],
        "test": [
            "mockito==1.2.1",
            "pytest==5.4.2",
            "pytest-cov==2.8.1",
            "pytest-aiohttp==0.3.0",
        ],
    },
    # To keep PyCharm from complaining about missing requirements:
    tests_require=[
        "mockito==1.2.1",
        "pytest==5.4.2",
        "pytest-cov==2.8.1",
        "pytest-aiohttp==0.3.0",
        "pytest-mock",
        "pytest-env",
        "attrdict",
    ],
)

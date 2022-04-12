from sphinx.setup_command import BuildDoc
cmdclass = {'build_sphinx': BuildDoc}
from setuptools import setup, find_packages


name = 'orchd-sdk'
version = open('src/orchd_sdk/VERSION').read().strip()
author = "Mathias Santos de Brito"

requirements = [
    'rx',
    'pydantic',
    'GitPython',
    'colorama'
]

test_requirements = [
    *requirements,
    'pytest',
    'pytest-asyncio',
    'coverage',
    'black',
    'mypy'
]

doc_requirements = [
    'sphinx',
    'sphinx_rtd_theme'
]

setup(
    name=name,
    version=version,
    description='SDK for Orchd Ecosystem Applications',
    keywords='service resource orchestration edge cloud',
    url='http://orchd.io',
    classifiers=[
        'License :: Other/Proprietary License',
        'Intended Audience :: Information Technology',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: System :: Distributed Computing'
    ],
    author=author,
    author_email='mathias.brito@me.com',

    install_requires=requirements,
    extras_require={
        'test': test_requirements,
        'doc': doc_requirements
    },
    package_dir={
        '': 'src',
    },
    packages=find_packages(where='src', exclude=('templates',)),
    package_data={'orchd_sdk': [
        'VERSION',
        'logger.ini',
    ]},
    entry_points={
        'console_scripts': [
            'orchd-sdk=orchd_sdk.cli:cli',
        ]
    }
)

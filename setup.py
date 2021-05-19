from setuptools import setup, find_packages

from os.path import join


version = open('src/orchd_sdk/VERSION').read().strip()

requirements = [
    'rx',
    'jsonschema',
]

test_requirements = [
    *requirements,
    'pytest',
    'pytest-asyncio',
    'coverage',
    'black',
    'mypy'
]

setup(
    name='orchd_sdk',
    version=version,
    description='SDK for Orchd Ecosystem Applications',
    keywords='service resource orchestration edge cloud',
    url='http://orchd.io',
    classifiers=[
        'License :: Other/Proprietary License',
        'Intended Audience :: Information Technology',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.8',
        'Topic :: System :: Distributed Computing'
    ],
    author='Mathias Santos de Brito',
    author_email='mathias.brito@me.com',

    install_requires=requirements,
    extras_require={
        'test': test_requirements
    },
    package_dir={
        '': 'src',
    },
    packages=find_packages(where='src'),
    package_data={'orchd_sdk': [
        'VERSION',
        'reaction.schema.json'
    ]}
)

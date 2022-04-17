# The MIT License (MIT)
# Copyright © 2022 <Mathias Santos de Brito>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from setuptools import setup, find_packages

name = 'orchd-sdk'
version = open('src/orchd_sdk/VERSION').read().strip()
author = "Mathias Santos de Brito"

requirements = [
    'reactivex',
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
        'Programming Language :: Python :: 3.10',
        'Topic :: System :: Distributed Computing'
    ],
    author=author,
    author_email='mathias.brito@me.com',

    install_requires=requirements,
    extras_require={
        'test': test_requirements,
        'docs': doc_requirements
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

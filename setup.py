import os
import sys
from setuptools import setup, find_packages

import plan_b as module

WINDOWS = sys.platform.lower().startswith("win")


def walker(base, *paths):
    file_list = set([])
    cur_dir = os.path.abspath(os.curdir)

    os.chdir(base)
    try:
        for path in paths:
            for dir_name, dirs, files in os.walk(path):
                for f in files:
                    file_list.add(os.path.join(dir_name, f))
    finally:
        os.chdir(cur_dir)

    return list(file_list)


requires = (
    'jira',
    'openpyxl',
    'XlsxWriter',
    'PyYAML>=4.2b1',
    'yarl',
    'python-dateutil',
    'sqlalchemy',
    'alembic',
    'asyncpg==0.18.2',
    'psycopg2-binary',
    'gino'
)


setup(
    name='plan_b',
    version=module.__version__,
    author=module.__author__,
    author_email=module.email,
    license=module.package_license,
    description=module.package_info,
    platforms="all",
    classifiers=(
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Internet',
        'Topic :: Software Development',
    ),
    long_description=open('README.md').read(),
    packages=find_packages(exclude=(
        'tests', 'tests.*', 'tests_performance', 'tests_migrations',
    )),
    package_data={
        module.__name__: walker(
            os.path.dirname(module.__file__),
        ),
    },
    entry_points={
        'console_scripts': [
            f'plan_b = {module.__name__}.cli:main',
            f'db_manage = {module.__name__}.db_manage:main',
        ]
    },
    install_requires=requires,
    extras_require={
        'develop': [
            'pytest<3.7',
            'pytest-cov',
        ],
    }
)

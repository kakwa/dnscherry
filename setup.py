#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:

import os
import re
import sys
from distutils.core import setup

# some install path variables
sysconfdir = os.getenv("SYSCONFDIR", "/etc")
datarootdir = os.getenv("DATAROOTDIR", sys.prefix)

data_dir = os.path.join(sys.prefix, 'share', 'dnscherry')
small_description = 'A simple web application to manage DNS zones'

# change requirements according to python version
if sys.version_info[0] == 2:
    install_requires = [
        'CherryPy >= 3.0.0',
        'dnspython',
        'Mako'
        ],
elif sys.version_info[0] == 3:
    install_requires = [
        'CherryPy >= 3.0.0',
        'dnspython3',
        'Mako'
        ],
else:
    print('unsupported version')
    exit(1)

try:
    f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
    description = f.read()
    f.close()
except IOError:
    description = small_description

try:
    license = open('LICENSE').read()
except IOError:
    license = 'MIT'

try:
    from setuptools import setup
    from setuptools.command.test import test as TestCommand

    class PyTest(TestCommand):
        def finalize_options(self):
            TestCommand.finalize_options(self)
            self.test_args = []
            self.test_suite = True

        def run_tests(self):
            # import here, cause outside the eggs aren't loaded
            import pytest
            errno = pytest.main(self.test_args)
            sys.exit(errno)

except ImportError:

    from distutils.core import setup
    PyTest = lambda x: x


# just a small function to easily install a complete directory
def get_list_files(basedir, targetdir):
    return_list = []
    for root, dirs, files in os.walk(basedir):
        subpath = re.sub(r'' + basedir + '[\/]*', '', root)
        files_list = []
        for f in files:
            files_list.append(os.path.join(root, f))
        return_list.append((os.path.join(targetdir, subpath), files_list))
    return return_list

resources_files = get_list_files(
    'resources',
    os.path.join(datarootdir, 'share', 'dnscherry')
    )

resources_files.append((
        os.path.join(sysconfdir, 'dnscherry'),
        ['conf/dnscherry.ini']
    ))

setup(
    name='dnscherry',
    zip_safe=False,
    version='0.1.0',
    author='Pierre-Francois Carpentier',
    author_email='carpentier.pf@gmail.com',
    packages=['dnscherry', 'dnscherry.auth'],
    data_files=resources_files,
    scripts=['scripts/dnscherryd'],
    url='https://github.com/kakwa/dnscherry',
    license=license,
    description=small_description,
    long_description=description,
    install_requires=install_requires,
    tests_require=['pytest'],
    extras_require={
            'auth_htpasswd': ['passlib'],
            'auth_ldap': ['python-ldap']
        },
    cmdclass={'test': PyTest},
    classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Web Environment',
            'Framework :: CherryPy',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: POSIX',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Topic :: Internet :: Name Service (DNS)',
        ]
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:

import os
import re
import sys
from distutils.core import setup

#some install path variables
sysconfdir = os.getenv("SYSCONFDIR", "/etc")
datarootdir = os.getenv("DATAROOTDIR", os.path.join(sys.prefix, 'share'))

data_dir = os.path.join(sys.prefix, 'share' ,'dnscherry')
small_description = 'A simple web application to manage DNS zones'

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
            #import here, cause outside the eggs aren't loaded
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

setup(
    name = 'dnscherry',
    version = '0.0.0',
    zip_safe=False,
    author = 'Pierre-Francois Carpentier',
    author_email = 'carpentier.pf@gmail.com',
    packages = ['dnscherry'],
    package_dir = {'dnscherry': 'resources'},
    data_files = get_list_files('resources', datarootdir),
    #scripts = ['scripts/asciigraph'],
    url = 'https://github.com/kakwa/dnscherry',
    license = license,
    description = small_description, 
    long_description = description,
    install_requires = [
        'CherryPy >= 3.0.0',
        'dnspython',
        'Mako'
        ],
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    classifiers=[
	'Development Status :: 4 - Beta',
	'Intended Audience :: System Administrators',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3']
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import unicode_literals

import pytest
import sys
import subprocess
from tempfile import NamedTemporaryFile as tempfile
import re

from sets import Set
from dnscherry import DnsCherry

import cherrypy
from cherrypy.process import plugins, servers
from cherrypy import Application
import logging

cherrypy.session = {}


def loadconf(configfile, instance):
    app = cherrypy.tree.mount(instance, '/', configfile)
    cherrypy.config.update(configfile)
    instance.reload(app.config)

class HtmlValidationFailed(Exception):
    def __init__(self, out):
        self.errors = out

def htmlvalidator(page):
    f = tempfile()
    stdout = tempfile()
    f.write(page.encode("utf-8"))
    f.seek(0)
    ret = subprocess.call(['./tests/html_validator.py', '-h', f.name], stdout=stdout)
    stdout.seek(0)
    out = stdout.read()
    f.close()
    stdout.close()
    print(out)
    if not re.search(r'Error:.*', out) is None:
        raise HtmlValidationFailed(out)

class BadModule():
    pass


# monkey patching cherrypy to disable config interpolation
def new_as_dict(self, raw=True, vars=None):
    """Convert an INI file to a dictionary"""
    # Load INI file into a dict
    result = {}
    for section in self.sections():
        if section not in result:
            result[section] = {}
        for option in self.options(section):
            value = self.get(section, option, raw=raw, vars=vars)
            try:
                value = cherrypy.lib.reprconf.unrepr(value)
            except Exception:
                x = sys.exc_info()[1]
                msg = ("Config error in section: %r, option: %r, "
                       "value: %r. Config values must be valid Python." %
                       (section, option, value))
                raise ValueError(msg, x.__class__.__name__, x.args)
            result[section][option] = value
    return result
cherrypy.lib.reprconf.Parser.as_dict = new_as_dict

class TestError(object):

    def testNominal(self):
        app = DnsCherry()
        loadconf('./tests/cfg/dnscherry.ini', app)

    def testDnsGet(self):
        app = DnsCherry()
        loadconf('./tests/cfg/dnscherry.ini', app)
        ret = app._refresh_zone('example.com')
        expected = [
            {'content': '192.168.0.16', 'type': 'A', 'class': 'IN', 'key': 'asda', 'ttl': '3600'},
            {'content': '192.168.0.4', 'type': 'A', 'class': 'IN', 'key': 'www', 'ttl': '3600'},
            {'content': '2001:db8:10::2', 'type': 'AAAA', 'class': 'IN', 'key': 'ns', 'ttl': '3600'},
            {'content': '192.168.0.20', 'type': 'A', 'class': 'IN', 'key': 'asds', 'ttl': '3600'},
            {'content': '192.168.0.11', 'type': 'A', 'class': 'IN', 'key': 'asdaaaa', 'ttl': '3600'},
            {'content': '192.168.0.4', 'type': 'A', 'class': 'IN', 'key': '123', 'ttl': '3600'},
            {'content': 'asd', 'type': 'CNAME', 'class': 'IN', 'key': 'asdaasd', 'ttl': '3600'},
        ]
        assert ret == expected

    def testLogger(self):
        app = DnsCherry()
        loadconf('./tests/cfg/dnscherry.ini', app)
        assert app._get_loglevel('debug') is logging.DEBUG and \
        app._get_loglevel('notice') is logging.INFO and \
        app._get_loglevel('info') is logging.INFO and \
        app._get_loglevel('warning') is logging.WARNING and \
        app._get_loglevel('err') is logging.ERROR and \
        app._get_loglevel('critical') is logging.CRITICAL and \
        app._get_loglevel('alert') is logging.CRITICAL and \
        app._get_loglevel('emergency') is logging.CRITICAL and \
        app._get_loglevel('notalevel') is logging.INFO

    def testAddDel(self):
        app = DnsCherry()
        loadconf('./tests/cfg/dnscherry.ini', app)
        try:
            app.add_record('test', '3600', 'A', 'example.com', '192.168.0.1')
        except cherrypy.HTTPRedirect as e:
            if e[0][0] != 'http://127.0.0.1:8080/?zone=example.com':
                return False
        try:
            app.del_record(['test;A;192.168.0.1;IN;3600'], 'example.com')
        except cherrypy.HTTPRedirect as e:
            if e[0][0] != 'http://127.0.0.1:8080/?zone=example.com':
                return False

    def testHtml(self):
        app = DnsCherry()
        loadconf('./tests/cfg/dnscherry.ini', app)
        pages = {
                'signin': app.signin(),
                'index': app.index(),
                }
        for page in pages:
            print(page)
            htmlvalidator(pages[page])


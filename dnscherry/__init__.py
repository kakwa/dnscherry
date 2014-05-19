#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
#
# The MIT License (MIT)
# DnsCherry
# Copyright (c) 2014 Carpentier Pierre-Francois

#generic imports
import sys
import re
import traceback
import logging
import logging.handlers
from operator import itemgetter
from socket import error as socket_error

#dnspython imports
import dns.query
import dns.zone
import dns.name
import dns.tsigkeyring
from dns.tsig import PeerBadKey
import dns.update
from dns.exception import DNSException
from dns.rdataclass import *
from dns.rdatatype import *

#cherrypy http framework imports
import cherrypy
from cherrypy.lib.httputil import parse_query_string

#mako template engines imports
from mako.template import Template
from mako import lookup

SESSION_KEY = '_cp_username'

# some custom exceptions
class NoRecordSelected(Exception):
    pass

class WrongDnsUpdateMethod(Exception):
    pass

class MissingParameter(Exception):
    def __init__(self, section, key):
        self.section = section
        self.key = key

class DnsCherry(object):

    def _get_param(self, section, key, config, default=None):
        """ Get configuration parameter "key" from config
        @str section: the section of the config file
        @str key: the key to get
        @dict config: the configuration (dictionnary)
        @str default: the default value if parameter "key" is not present
        @rtype: str (value of config['key'] if present default otherwith
        """
        if section in config and key in config[section]:
            return config[section][key]
        if not default is None:
            return default
        else:
            raise MissingParameter(section, key)

    def reload(self, config = None):
        """ load/reload the configuration
        """

        try:
            # definition of the template directory
            self.template_dir = self._get_param('resources', 'template_dir', config)
            # configure the default zone (zone displayed by default)
            self.zone_default = self._get_param('dns', 'default.zone', config)
            # configure the default ttl for the form
            self.default_ttl = self._get_param('dns', 'default.ttl', config, '86400')
            # configure the list of dns entry type to display
            self.type_displayed = re.split('\W+', 
                        self._get_param('dns', 'type.displayed', config, 'CNAME, A, AAAA')
                    )
            # configure the list of dns entry type a user can write
            self.type_written = re.split('\W+',
                        self._get_param('dns', 'type.written', config, 'CNAME, A, AAAA')
                    )

            # set if redirect on zone page after add or if
            # display a summary of the added entries
            if self._get_param('global', 'form.add.redirect', config, 'on') == 'on':
                self.form_add_redirect = True
            else:
                self.form_add_redirect = False

            # same for delete
            if self._get_param('global', 'form.del.redirect', config, 'on') == 'on':
                self.form_del_redirect = True
            else:
                self.form_del_redirect = False

            # log configuration handling
            # get log level 
            # (if not in configuration file, log level is set to debug)
            level = self._get_loglevel(self._get_param('global', 'log.level', config, 'debug'))

            # log format for syslog
            syslog_formatter = logging.Formatter(
                    "dnscherry[%(process)d]: %(message)s")

            access_handler = self._get_param('global', 'log.access_handler', config, 'syslog')

            # replace access log handler by a syslog handler
            if access_handler == 'syslog':
                cherrypy.log.access_log.handlers = []
                handler = logging.handlers.SysLogHandler(address = '/dev/log',
                        facility='user')
                handler.setFormatter(syslog_formatter)
                cherrypy.log.access_log.addHandler(handler)

            # if file, we keep the default
            elif access_handler == 'file':
                pass

            # replace access log handler by a null handler
            elif access_handler == 'none':
                cherrypy.log.access_log.handlers = []
                handler = logging.NullHandler()
                cherrypy.log.access_log.addHandler(handler)

            error_handler = self._get_param('global', 'log.error_handler', config, 'syslog')

            # replacing the error handler by a syslog handler
            if error_handler == 'syslog':
                cherrypy.log.error_log.handlers = []

                # redefining log.error method because cherrypy does weird
                # things like adding the date inside the message 
                # or adding space even if context is empty 
                # (by the way, what's the use of "context"?)
                def syslog_error(msg='', context='', 
                        severity=logging.INFO, traceback=False):
                    if traceback:
                        msg += cherrypy._cperror.format_exc()
                    if context == '':
                        cherrypy.log.error_log.log(severity, msg)
                    else:
                        cherrypy.log.error_log.log(severity, 
                                ' '.join((context, msg)))
                cherrypy.log.error = syslog_error

                handler = logging.handlers.SysLogHandler(address = '/dev/log',
                        facility='user')
                handler.setFormatter(syslog_formatter)
                cherrypy.log.error_log.addHandler(handler)

            # if file, we keep the default
            elif error_handler == 'file':
                pass

            # replacing the error handler by a null handler
            elif error_handler == 'none':
                cherrypy.log.error_log.handlers = []
                handler = logging.NullHandler()
                cherrypy.log.error_log.addHandler(handler)

            # set log level
            cherrypy.log.error_log.setLevel(level)
            cherrypy.log.access_log.setLevel(level)

            # preload templates
            self.temp_lookup = lookup.TemplateLookup(
                    directories=self.template_dir, input_encoding='utf-8'
                    )
            self.temp_index = self.temp_lookup.get_template('index.tmpl')
            self.temp_result = self.temp_lookup.get_template('result.tmpl')
            self.temp_error = self.temp_lookup.get_template('error.tmpl')
            self.temp_login = self.temp_lookup.get_template('login.tmpl')

            # loading the authentification module
            auth_module = self._get_param('auth', 'auth.module', config)
            auth = __import__(auth_module, globals(), locals(), ['Auth'], -1)
            self.auth = auth.Auth(config['auth'], cherrypy.log)

        except MissingParameter as e:
            cherrypy.log.error(
                msg = "dnscherry failure, "\
                    "missing parameter '%(param)s' "\
                    "in section '%(section)s'" % {
                        'param': e.key,
                        'section': e.section
                    },
                severity = logging.ERROR
                )
            exit(1)


            
        # some static messages
        self.sucess_message_add = """New record(s) successfully added!"""
        self.sucess_message_del = """Record(s) successfully deleted!"""

        # zones section parsing
        self.zone_list = {}
        self._parse_zones(config)

    def _get_loglevel(self, level):
        """ return logging level object
        corresponding to a given level passed as
        a string
        """
        if level == 'debug':
            return logging.DEBUG
        elif level == 'notice':
            return logging.NOTICE
        elif level == 'info':
            return logging.INFO
        elif level == 'warning' or level == 'warn':
            return logging.WARNING
        elif level == 'error' or level == 'err':
            return logging.ERROR
        elif level == 'critical' or level == 'crit':
            return logging.CRITICAL
        elif level == 'alert':
            return logging.ALERT
        elif level == 'emergency' or level == 'emerg':
            return logging.EMERGENCY
        else:
            return logging.INFO

    def _select_algorithm(self, algo):
        """ get the dns.tsig object corresponding the 
        the tsig algorithme choosen
        """

        # case insensitive
        algo = algo.lower()

        if   algo == "hmac-md5":
            return dns.tsig.HMAC_MD5
        elif algo == "hmac-sha1":
            return dns.tsig.HMAC_SHA1
        elif algo == "hmac-sha224":
            return dns.tsig.HMAC_SHA224
        elif algo == "hmac-sha256":
            return dns.tsig.HMAC_SHA256
        elif algo == "hmac-sha384":
            return dns.tsig.HMAC_SHA384
        elif algo == "hmac-sha512":
            return dns.tsig.HMAC_SHA512
        else:
            return None

    def _parse_zones(self, config):
        """dedicated parser for ['dns.zones'] section
        in .ini file.
        """

        # each entry in dns.zones is a zone parameters
        # format <key>.<zone> = '<value>'
        # list of the keys: ip, algorithm, key
        for entry in config['dns.zones']:

            # split at the first dot
            key, sep, zone = entry.partition('.')
            value = config['dns.zones'][entry]

            # create or complete the zone entry
            # in self.zone_list, depending if
            # it's already initialized
            # 
            # self.zone_list is a dict of dict, 
            # ex:
            # self.zone_list = {'example.com': 
            #               {   'ip': '127.0.0.1', 
            #                   'key': 'ujeGPu0NCU1TO9fQKiiuXg==',
            #                   'algorithm': 'hmac-md5'
            #               },
            #   }
            if zone in self.zone_list:
                self.zone_list[zone][key] = value 
            else:
                self.zone_list[zone] = { key : value } 

    def _validate_domain(self, domain):
        """ validate that a domain string really looks like a domain string
        """
        if re.match('^(([a-zA-Z0-9\-]{1,63}\.?)+([a-zA-Z0-9\-]+)){1,255}$', 
                domain):
            return True
        else:
            return False

    def _refresh_zone(self, zone = None):
        """get the dns zone 'zone'.
           It only lists records which type are in 'self.type_written'.
           'zone' must be correctly configured in 'self.zone_list'

           @str zone: the zone name to refresh
           @rtype: list of hash {'key', 'class', 'type', 'ttl', 'content'}
        """
        # zone is defined by the query string parameter
        # if query string is empty, use the default zone
        if zone is None:
            zone = self.zone_default
        # get the zone from the dns
        self.zone = dns.zone.from_xfr(dns.query.xfr(
            self.zone_list[zone]['ip'], zone))
        records = []
        # get all the records in a list of hash 
        # {'key', 'class', 'type', 'ttl', 'content'}
        for name, node in self.zone.nodes.items():
            rdatasets = node.rdatasets
            for rdataset in rdatasets:
                for rdata in rdataset:
                    record = {}
                    record['key'] = name.to_text(name)
                    record['class'] = dns.rdataclass.to_text(rdataset.rdclass)
                    record['type'] = dns.rdatatype.to_text(rdataset.rdtype)
                    record['ttl'] = str(rdataset.ttl)
                    record['content'] =  rdata.to_text()
                    # filter by record type
                    if record['type'] in self.type_displayed:
                        records.append(record)
        return records

    def _manage_record(self, key=None, ttl=None, type=None,
            zone=None, content=None, action=None):
        """ add or delete a given record
        """
        
        keyring = dns.tsigkeyring.from_text({
            zone : self.zone_list[zone]['key']
        })

        update = dns.update.Update(zone + '.' , 
                keyring=keyring,
                keyalgorithm=self._select_algorithm(
                    self.zone_list[zone]['algorithm']
                    )
                )

        if action == 'add':
            ttl = int(ttl)
            content = str(content)
            type = str(type)
            update.add(key, ttl, type, content)
        elif action == 'del':
            type = str(type)
            update.delete(key, type)
        else:
            raise WrongDnsUpdateMethod 

        response = dns.query.tcp(update, self.zone_list[zone]['ip'])

    def _reraise(self, exception):
        """ reraise a given exception"""
        raise exception
    
    def _error_handler(self, exception, zone=''):
        """ exception handling function, takes an exception
        and returns the right error page and emits a log
        """

        # log the traceback as 'debug'
        cherrypy.log.error(
                msg = '',
                severity = logging.DEBUG,
                traceback= True
                )

        zone = str(zone)

        # log and error page handling
        def render_error(alert, message, zone=zone):
            if alert == 'danger':
                severity = logging.ERROR
            elif alert == 'warning':
                severity = logging.WARNING
            else:
                severity = logging.CRITICAL

            cherrypy.log.error(
                    msg = message,
                    severity = severity
                    )

            return self.temp_error.render(
                        logout_button = self.auth.logout_button,
                        alert = alert,
                        message = message,
                        zone_list = self.zone_list,
                        current_zone = zone
                )

        # first, we check if the zone name is valid
        if not self._validate_domain(zone):
            cherrypy.response.status = 400
            return render_error(
                alert = 'warning',
                message = 'Bad zone name.',
                zone = self.zone_default
            )

        # reraise the exception
        try:
            self._reraise(exception)

        # error handling
        except dns.exception.FormError:
            cherrypy.response.status = 500 
            alert = 'danger'
            message = 'Unable to get Zone "' + zone +  '".'
            return render_error(alert, message)

        except socket_error:
            cherrypy.response.status = 500 
            alert = 'danger'
            message = 'Unable to contact DNS.'
            return render_error(alert, message)

        except KeyError:
            cherrypy.response.status = 400
            alert = 'warning'
            message = 'Zone "' + zone +  '" not configured.'
            return render_error(alert, message)

        except PeerBadKey:
            cherrypy.response.status = 500 
            alert = 'danger'
            message = 'Modification on zone "' + zone +  '" refused by DNS.'
            return render_error(alert, message)

        except dns.exception.SyntaxError:
            cherrypy.response.status = 400 
            alert = 'warning'
            message = 'Wrong form data, bad format.'
            return render_error(alert, message)

        except NoRecordSelected:
            cherrypy.response.status = 400 
            alert = 'warning'
            message = 'No record selected.'
            return render_error(alert, message)

        except UnknownRdatatype:
            cherrypy.response.status = 500 
            alert = 'danger'
            message = 'Unknown record type'
            return render_error(alert, message)

        except:
            cherrypy.response.status = 500 
            alert = 'danger'
            message = 'Unkwown error.'
            return render_error(alert, message)

    @cherrypy.expose
    def signin(self):
        """simple signin page
        """
        return self.temp_login.render()

    @cherrypy.expose
    def login(self, login, password):
        """login page
        """
        if self.auth.check_credentials(login, password):
            message = "login success for user '%(user)s'" % {
                'user': login
            }
            cherrypy.log.error(
                msg = message,
                severity = logging.INFO
            )
            cherrypy.session[SESSION_KEY] = cherrypy.request.login = login
            raise cherrypy.HTTPRedirect("/")
        else:
            message = "login failed for user '%(user)s'" % {
                'user': login
            }
            cherrypy.log.error(
                msg = message,
                severity = logging.WARNING
            )
            raise cherrypy.HTTPRedirect("/signin")

    @cherrypy.expose
    def logout(self):
        """ logout page 
        """
        user = self.auth.end_session()
        message = "user '%(user)s' logout" % {
            'user': user
        }
        cherrypy.log.error(
            msg = message,
            severity = logging.INFO
        )

        raise cherrypy.HTTPRedirect("/signin")

    @cherrypy.expose
    def index(self, zone=None, **params):
        """main page rendering
        """

        user = 'unknown'

        user = self.auth.check_auth()

        parse_query_string(cherrypy.request.query_string)
        # zone is defined by the query string parameter
        # if query string is empty, use the default zone
        if zone is None:
            zone = self.zone_default
        try:
            records = self._refresh_zone(zone)
        # exception handling if impossible to get the zone
        # (dns unavailable, misconfiguration, etc)
        except Exception as e:
            return self._error_handler(e, zone)

        return self.temp_index.render(
                logout_button = self.auth.logout_button,
                records=records, 
                zone_list=self.zone_list,
                default_ttl = self.default_ttl,
                type_written = self.type_written,
                current_zone = zone
                )

    @cherrypy.expose
    def del_record(self, record=None, zone=None):
        """delete records page
        """

        user = 'unknown'
        user = self.auth.check_auth()

        # if we select only on entry, it's a string and not a list
        if record is None:
            return self._error_handler(NoRecordSelected, zone)
        elif not isinstance(record, list):
            record = [record]

        deleted_records = []

        for r in record:
            key = (r.split(';'))[0]
            type = (r.split(';'))[1]
            content = (r.split(';'))[2]
            dns_class = (r.split(';'))[3]
            ttl = (r.split(';'))[4]
            del_record = {
                   'key': key,
                   'ttl': ttl,
                   'class': dns_class,
                   'type': type,
                   'content': content
                   }
            deleted_records.append(del_record)
            try:
                self._manage_record(key=key, type=type, zone=zone, action='del')
            except Exception as e:
                return self._error_handler(e, zone)

            message = "Record '%(key)s %(ttl)s %(class)s %(type)s \
%(content)s' removed by '%(user)s' on zone '%(zone)s'" % {
                    'key': key,
                    'ttl': ttl,
                    'class': 'IN',
                    'type': type,
                    'content': content,
                    'zone': zone,
                    'user': user 
                    }

            cherrypy.log.error(
                msg = message,
                severity = logging.INFO
            )
        
        if self.form_del_redirect:
            raise cherrypy.HTTPRedirect("/?zone=" + zone)
        else:
            return self.temp_result.render(
                    logout_button = self.auth.logout_button,
                    records = deleted_records,
                    zone_list = self.zone_list,
                    current_zone = zone,
                    message = self.sucess_message_del,
                    alert = 'success',
                    action = 'del'
                    )

    @cherrypy.expose
    def add_record(self, key=None, ttl=None, type=None, 
            zone=None, content=None):
        """ add record page
        """
        
        user = 'unknown'
        user = self.auth.check_auth()

        try:
            self._manage_record(key, ttl, type, zone, content, 'add')
        except Exception as e:
            return self._error_handler(e, zone)

        new_record = [{
                'key': key,
                'ttl': ttl,
                'class': 'IN',
                'type': type,
                'content': content
                }]

        message = "Record '%(key)s %(ttl)s %(class)s %(type)s \
%(content)s' added by '%(user)s' on zone '%(zone)s'" % {
                    'key': key,
                    'ttl': ttl,
                    'class': 'IN',
                    'type': type,
                    'content': content,
                    'zone': zone,
                    'user': user
                    }

        cherrypy.log.error(
            msg = message,
            severity = logging.INFO
         )

        if self.form_add_redirect:
            raise cherrypy.HTTPRedirect("/?zone=" + zone)
        else:
            return self.temp_result.render(
                    logout_button = self.auth.logout_button,
                    records = new_record,
                    zone_list = self.zone_list,
                    current_zone = zone,
                    message = self.sucess_message_add,
                    alert = 'success',
                    action = 'add'
                    )


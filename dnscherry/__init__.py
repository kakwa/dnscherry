#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:

#generic imports
import json
import sys
import re
import traceback
from operator import itemgetter

#dnspython imports
import dns.query
import dns.zone
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

class NoRecordSelected(Exception):
    pass

class WrongDnsUpdateMethod(Exception):
    pass

class DnsCherry(object):

    def reload(self, config = None):

        # definition of the template directory
        self.template_dir = config['resources']['template_dir']
        # configure the default zone (zone displayed by default)
        self.zone_default = config['dns']['default.zone']
        # configure the default ttl for the form
        self.default_ttl = config['dns']['default.ttl']
        # configure the list of dns entry type to display
        self.type_displayed = re.split('\W+', 
                    config['dns']['type.displayed']
                )
        # configure the list of dns entry type a user can write
        self.type_written = re.split('\W+',
                    config['dns']['type.written']
                )
            
        # preload templates
        self.temp_lookup = lookup.TemplateLookup(
                directories=self.template_dir, input_encoding='utf-8'
                )
        self.temp_index = self.temp_lookup.get_template('index.tmpl')
        self.temp_result = self.temp_lookup.get_template('result.tmpl')
        self.temp_error = self.temp_lookup.get_template('error.tmpl')

        # some static messages
        self.sucess_message_add = """New record(s) successfully added!"""
        self.sucess_message_del = """Record(s) successfully deleted!"""

        # zones section parsing
        self.zone_list = {}
        self._parse_zones(config)

    def _select_algorithm(self, algo):
        if algo.lower() == "hmac-md5":
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
        # return the list of records sorted by record type
        return sorted(records, key=itemgetter('type'))  

    def _manage_record(self, key=None, ttl=None, type=None,
            zone=None, content=None, action=None):
        
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
        raise exception
    
    def _error_handler(self, exception, zone=''):
        #print(traceback.format_exc())
        zone = str(zone)
        try:
            self._reraise(exception)
        except dns.exception.FormError:
            cherrypy.response.status = 500 
            return self.temp_error.render(
                        alert = 'danger',
                        message = 'Unable to get Zone "' + zone +  '".',
                        zone_list = self.zone_list,
                        current_zone = zone
                )

        except KeyError:
            cherrypy.response.status = 400
            return self.temp_error.render(
                        alert = 'warning',
                        message = 'Zone "' + zone +  '" not configured.',
                        zone_list = self.zone_list,
                        current_zone = zone
                )
        except PeerBadKey:
            cherrypy.response.status = 500 
            return self.temp_error.render(
                        alert = 'danger',
                        message = 'Modification on zone "' + zone +  '" refused by DNS.',
                        zone_list = self.zone_list,
                        current_zone = zone
                )
        except dns.exception.SyntaxError:
            cherrypy.response.status = 400 
            return self.temp_error.render(
                        alert = 'warning',
                        message = 'Wrong form data, bad format.',
                        zone_list = self.zone_list,
                        current_zone = zone
                )
        except NoRecordSelected:
            cherrypy.response.status = 400 
            return self.temp_error.render(
                        alert = 'warning',
                        message = 'No record selected.',
                        zone_list = self.zone_list,
                        current_zone = zone
                )

        except UnknownRdatatype:
            cherrypy.response.status = 500 
            return self.temp_error.render(
                        alert = 'danger',
                        message = 'Unknown record type',
                        zone_list = self.zone_list,
                        current_zone = zone
                )
        except:
            cherrypy.response.status = 500 
            return self.temp_error.render(
                        alert = 'danger',
                        message = 'Unkwown error.',
                        zone_list = self.zone_list,
                        current_zone = zone
                )

    @cherrypy.expose
    def index(self, zone=None, **params):
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
                records=records, 
                zone_list=self.zone_list,
                default_ttl = self.default_ttl,
                type_written = self.type_written,
                current_zone = zone
                )

    @cherrypy.expose
    def del_record(self, record=None, zone=None):

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

    
        return self.temp_result.render(
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


        return self.temp_result.render(
                records = new_record,
                zone_list = self.zone_list,
                current_zone = zone,
                message = self.sucess_message_add,
                alert = 'success',
                action = 'add'
                )


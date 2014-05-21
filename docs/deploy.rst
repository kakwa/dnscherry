Deploy
======

Launching DnsCherry
-------------------

DnsCherry can be launch using cherrypy internal webserver:


.. sourcecode:: bash

    # dnscherryd help
    $ dnscherryd -h
    Usage: dnscherryd [options]
    
    Options:
      -h, --help            show this help message and exit
      -c CONFIG, --config=CONFIG
                            specify config file
      -d                    run the server as a daemon
      -e ENVIRONMENT, --environment=ENVIRONMENT
                            apply the given config environment
      -f                    start a fastcgi server instead of the default HTTP
                            server
      -s                    start a scgi server instead of the default HTTP server
      -x                    start a cgi server instead of the default HTTP server
      -p PIDFILE, --pidfile=PIDFILE
                            store the process id in the given file
      -P PATH, --Path=PATH  add the given paths to sys.path

    # launching dnscherryd
    $ dnscherryd -c /etc/dnscherry/dnscherry.ini

Dns Configuration
-----------------

This section presents the configuration of a zone **example.com**, change it with your own zone name. 

Creation of the tsig key
~~~~~~~~~~~~~~~~~~~~~~~~

To create a tsig key, use the following commands:

.. sourcecode:: bash

   $ dnssec-keygen -a HMAC-SHA512 -b 512 -n HOST example.com.
   # it creates two files:
   $ ls K*
   Kexample.com.+165+27879.key  Kexample.com.+165+27879.private

   # content
   $ cat K*.private
   Private-key-format: v1.3
   Algorithm: 165 (HMAC_SHA512)
   Key: oWko9cBK6yUDnhl8R6g0drseVc2t9erYIiHD/u9t31iMYR+rbF5Y7IXeVdGCwEDe3fpQVYWvZosUzScZ5VStLA==
   Bits: AAA=
   Created: 20140521080238
   Publish: 20140521080238
   Activate: 20140521080238

The important field for us is **Key**, it's this field which will be used in the dns server and DnsCherry.

Bind server tsig configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure bind server to use this key:

.. sourcecode:: none

    key example.com. {
        algorithm       hmac-sha512;
        secret "oWko9cBK6yUDnhl8R6g0drseVc2t9erYIiHD/u9t31iMYR+rbF5Y7IXeVdGCwEDe3fpQVYWvZosUzScZ5VStLA==";
    };
    
    zone "example.com" {
        type master;
        file "/var/lib/bind/db.example.com";
        allow-update { key "example.com."; };
    };

.. warning::

    Bind must have writing rights on **/var/lib/bind/db.example.com** and **/var/lib/bind/**.

DnsCherry configuration
~~~~~~~~~~~~~~~~~~~~~~~

Configure the zone in DnsCherry:

.. sourcecode:: ini

    [dns.zones]

    #####################################
    # parameters for zone "example.com" #
    #####################################
    # dns server ip
    ip.example.com = '127.0.0.1'
    # hmac algorithm
    algorithm.example.com = 'hmac-sha512'
    # hmac key
    key.example.com = 'oWko9cBK6yUDnhl8R6g0drseVc2t9erYIiHD/u9t31iMYR+rbF5Y7IXeVdGCwEDe3fpQVYWvZosUzScZ5VStLA=='

You can configure multiple zones by adding **ip.<your domain>**, **algorithm.<your domain>** 
and **key.<your domain>** in the **[dns.zones]** section.

example:

.. sourcecode:: ini

    [dns.zones]

    ip.example.com = '127.0.0.1'
    algorithm.example.com = 'hmac-sha512'
    key.example.com = 'oWko9cZosUzScZ5VStLA=='

    ip.mydomain.org = '192.168.0.1'
    algorithm.mydomain.org = 'hmac-md5'
    key.mydomain.org = 'oWko9caaaafdeZosUzScZ5VStLA=='

Other dns parameters
~~~~~~~~~~~~~~~~~~~~

DnsCherry has other dns parameters which must be provided:

.. sourcecode:: ini

    # other dns parameters
    [dns]
    # the default selected zone
    default.zone = 'example.com'
    # record types to display
    type.displayed = 'A, AAAA, CNAME, MX'
    # record types available for new records
    type.written = 'A, AAAA, CNAME, MX'
    # default ttl for new records
    default.ttl = '3600'

Supported algorithms
~~~~~~~~~~~~~~~~~~~~

DnsCherry supports the following algorithms:

* hmac-md5
* hmac-sha1
* hmac-sha224
* hmac-sha256
* hmac-sha384
* hmac-sha512

Logs
----

DnsCherry has two loggers, one for errors and actions (login, del/add, logout...) and one for access logs.
Each logger can be configured to log to syslog, file or be unactivated. 

.. warning::

    you can't set a logger to log both in file and syslog

Syslog configuration:

.. sourcecode:: ini

    [global]

    # logger syslog for access log 
    log.access_handler = 'syslog'
    # logger syslog for error and dnscherry log 
    log.error_handler = 'syslog'

File configuration:

.. sourcecode:: ini

    [global]

    # logger syslog for access log 
    log.access_handler = 'file'
    # logger syslog for error and dnscherry log 
    log.error_handler = 'file'
    # access log file
    log.access_file = '/tmp/dnscherry_access.log'
    # error and dnscherry log file
    log.error_file = '/tmp/dnscherry_error.log'



Disable logs:

.. sourcecode:: ini

    [global]

    # logger syslog for access log 
    log.access_handler = 'none'
    # logger syslog for error and dnscherry log 
    log.error_handler = 'none'

Set log level:

.. sourcecode:: ini

    [global]

    # log level
    log.level = 'info'

WebServer
---------

Cherrypy
~~~~~~~~

Nginx
~~~~~

Apache
~~~~~~

Init Script
-----------

Sample init script for Debian:

.. literalinclude:: ../goodies/init-debian
   :language: bash

This init script is available in **goodies/init-debian**.

DnsCherry configuration file
----------------------------

.. literalinclude:: ../conf/dnscherry.ini
   :language: ini


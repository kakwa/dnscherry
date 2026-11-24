Deploy
======

Launching DnsCherry
-------------------

Run the bundled CherryPy server (see ``dnscherryd -h`` for FastCGI, SCGI, CGI, daemon mode, and other options)::

    dnscherryd -c /etc/dnscherry/dnscherry.ini

DNS configuration
-------------------

Examples below use zone **example.com**; substitute your zone name.

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

Use the **Key** value in both BIND and DnsCherry.

Bind server TSIG configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure Bind server to use this key:

.. sourcecode:: none

    key example.com. {
        algorithm       hmac-sha512;
        secret "oWko9cBK6yUDnhl8R6g0drseVc2t9erYIiHD/u9t31iMYR+rbF5Y7IXeVdGCwEDe3fpQVYWvZosUzScZ5VStLA==";
    };
    
    zone "example.com" {
        type master;
        file "/var/lib/bind/db.example.com";
        allow-update { key "example.com."; };
        
        // In case you have an 'allow-transfer { "none"; };' in options
        //allow-transfer { <dnscherry ip>; };
    };

.. warning::

    The user running bind must have writing rights on **/var/lib/bind/db.example.com** and **/var/lib/bind/**.

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
    # dns server port (optional, default 53)
    port.example.com = 53
    # hmac algorithm
    algorithm.example.com = 'hmac-sha512'
    # hmac key
    key.example.com = 'oWko9cBK6yUDnhl8R6g0drseVc2t9erYIiHD/u9t31iMYR+rbF5Y7IXeVdGCwEDe3fpQVYWvZosUzScZ5VStLA=='

You can configure multiple zones by adding the following parameters in the **[dns.zones]** section:

* **ip.<your domain>**
* **port.<your domain>** (optional, default 53)
* **algorithm.<your domain>**
* **key.<your domain>**

example:

.. sourcecode:: ini

    [dns.zones]

    ip.example.com = '127.0.0.1'
    port.example.com = 53
    algorithm.example.com = 'hmac-sha512'
    key.example.com = 'oWko9cZosUzScZ5VStLA=='

    ip.mydomain.org = '192.168.0.1'
    port.mydomain.org = 5353
    algorithm.mydomain.org = 'hmac-md5'
    key.mydomain.org = 'oWko9caaaafdeZosUzScZ5VStLA=='

Supported algorithms
~~~~~~~~~~~~~~~~~~~~

DnsCherry supports the following algorithms:

* hmac-md5
* hmac-sha1
* hmac-sha224
* hmac-sha256
* hmac-sha384
* hmac-sha512

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

Logs
----

Two log channels: application (errors and actions such as login and record changes) and HTTP access. Each can write to syslog, a file, or be disabled.

.. warning::

    A single logger cannot use both file and syslog at once.

Syslog:

.. sourcecode:: ini

    [global]

    log.access_handler = 'syslog'
    log.error_handler = 'syslog'

File:

.. sourcecode:: ini

    [global]

    log.access_handler = 'file'
    log.error_handler = 'file'
    # access log file
    log.access_file = '/tmp/dnscherry_access.log'
    # error and dnscherry log file
    log.error_file = '/tmp/dnscherry_error.log'

Disable logs:

.. sourcecode:: ini

    [global]

    log.access_handler = 'none'
    log.error_handler = 'none'

Set log level:

.. sourcecode:: ini

    [global]

    # log level
    log.level = 'info'

Other DnsCherry parameters
--------------------------

.. sourcecode:: ini

    [global]
    
    # bind address
    server.socket_host = '127.0.0.1'
    # port
    server.socket_port = 8080
    # number of threads
    server.thread_pool = 8
    #don't show traceback on error
    request.show_tracebacks = False
    
    # session configuration
    # activate session
    tools.sessions.on = True
    # session timeout
    tools.sessions.timeout = 10
    # file session storage(to use if multiple processes, 
    # default is in RAM and per process)
    #tools.sessions.storage_type = "file"
    # session 
    #tools.sessions.storage_path = "/var/lib/dnscherry/sessions"
    
    # resources parameters
    [resources]
    # templates directory
    template_dir = '/usr/share/dnscherry/templates/'
    
    # enable cherrypy static handling
    # to comment if static content are handled otherwise
    [/static]
    tools.staticdir.on = True
    tools.staticdir.dir = '/usr/share/dnscherry/static/'

Reverse proxy
-------------

For production, run DnsCherry behind nginx or Apache (TLS, HTTP/2, hardening). Terminate TLS at the proxy and forward to DnsCherry on localhost.

CherryPy built-in server
~~~~~~~~~~~~~~~~~~~~~~~~

Fine for testing. Limitations: no TLS in CherryPy itself, non-privileged ports unless configured otherwise.

Listen on all interfaces:

.. sourcecode:: ini

    [global]

    server.socket_host = '0.0.0.0'
    server.socket_port = 8080
 
Nginx
~~~~~

.. literalinclude:: ../goodies/nginx.conf
   :language: none

Apache
~~~~~~

.. literalinclude:: ../goodies/apache.conf
   :language: none

Lighttpd
~~~~~~~~

.. literalinclude:: ../goodies/lighttpd.conf
   :language: none

DnsCherry configuration file
----------------------------

.. literalinclude:: ../conf/dnscherry.ini
   :language: ini

Init Script
-----------

Sample init script for Debian:

.. literalinclude:: ../goodies/init-debian
   :language: bash

This init script is available in **goodies/init-debian**.

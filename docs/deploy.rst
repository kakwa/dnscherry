Deploy
======

Dns Configuration
-----------------

Create a Dns Tsig Key
~~~~~~~~~~~~~~~~~~~~~

This section shows the configuration of a zone **example.com**, change it with your own zone name. 

.. sourcecode:: bash

   $ dnssec-keygen -a HMAC-SHA512 -b 512 -n HOST example.com.

   # creates two files:
   $ ls K*
   Kexample.com.+165+27879.key  Kexample.com.+165+27879.private

   # content
   cat K*.private
   Private-key-format: v1.3
   Algorithm: 165 (HMAC_SHA512)
   Key: oWko9cBK6yUDnhl8R6g0drseVc2t9erYIiHD/u9t31iMYR+rbF5Y7IXeVdGCwEDe3fpQVYWvZosUzScZ5VStLA==
   Bits: AAA=
   Created: 20140521080238
   Publish: 20140521080238
   Activate: 20140521080238

The important field for us is **Key**.

Configure bind to use this key:

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

Bind must have writting rights on **/var/lib/bind/db.example.com** and **/var/lib/bind/**

Configure the zone in dnscherry:

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


WebServer
---------

Cherrypy
~~~~~~~~

Nginx
~~~~~

Apache
~~~~~~

Logs
----

Init Script
-----------

Sample init script for Debian:

.. literalinclude:: ../goodies/init-debian
   :language: bash

This init script is available in **goodies/init-debian**.



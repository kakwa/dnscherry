Install
=======

From the sources
----------------

Download the latest release from `GitHub <https://github.com/kakwa/dnscherry/releases>`_.

.. sourcecode:: bash

    $ tar -xf dnscherry*.tar.gz
    $ cd dnscherry*
    $ python setup.py install

From Pypi
---------

.. sourcecode:: bash 

    $ pip install dnscherry

or

.. sourcecode:: bash

    $ easy_install dnscherry 

Installed files
---------------

DnsCherry install directories are:

* **/etc/dnscherry/** (configuration)
* **dist-package** or **site-packages** of your distribution (DnsCherry modules)
* **/usr/share/dnscherry/** (static content (css, js, images...) and templates)

These directories can be changed by exporting the following variables before launching the install command:

.. sourcecode:: bash

    #optional, default sys.prefix (/usr/ on most Linux)
    $ export DATAROOTDIR=/usr/local/ 
    #optional, default /etc/
    $ export SYSCONFDIR=/usr/local/etc/ 


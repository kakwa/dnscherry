Install
=======

From PyPI
---------

.. sourcecode:: bash

    pip install dnscherry

From source
-----------

Download a release from `GitHub <https://github.com/kakwa/dnscherry/releases>`_::

    tar -xf dnscherry*.tar.gz
    cd dnscherry*
    python setup.py install

Installed layout
------------------

Default locations:

* ``/etc/dnscherry/`` — configuration
* Python ``site-packages`` (or distro equivalent) — DnsCherry modules
* ``<prefix>/share/dnscherry/`` — static files and templates (under ``DATAROOTDIR``)

Override install paths by setting environment variables before ``setup.py install``:

.. sourcecode:: bash

    # optional; default is sys.prefix (often /usr)
    export DATAROOTDIR=/usr/local

    # optional; default is /etc
    export SYSCONFDIR=/usr/local/etc

==============
django-netezza
==============

*FYI. I no longer have access to Netezza, so I'm not working on this anymore.*

------------------------------------------------------------------------------

A Django_ Netezza DB backend that uses ODBC by employing
the pyodbc_ library.

.. _Django: http://djangoproject.com/
.. _pyodbc: http://pyodbc.sourceforge.net

Currently, this is in a very, very experimental state. For one thing, I've only
tested this with read-only operations, because that's all I need at the moment.
I have only tried very simple models and simple queries and have not tested
anything with foreign keys, full-text search, etc.

Dependencies
============

* Django 1.3
* pyodbc 2.1.8 or newer
* Netezza ODBC driver

Installation
============

 1. Install pyodbc.

 2. Add the directory where you have copied the project files to your Python
    path. So, for example, if you have the following directory structure::

        /home/user/src/django-netezza
            |
            +- netezza
                  |
                  +- pyodbc

    you should add ``/home/user/src/django-netezza`` to you Python module search
    path. One way to do this is setting the ``PYTHONPATH`` environment
    variable::

       $ export PYTHONPATH=/home/user/src/django-netezza

 3. Now you can point the ``ENGINE`` setting in the settings file used
    by your Django application or project to the ``'netezza.pyodbc'``
    module path::

        DATABASES = {
            'default': {
                'OPTIONS': {'dsn': 'NETEZZA'},
                'ENGINE': 'netezza.pyodbc',
            },
        }

License
=======

New BSD LICENSE

Credits
=======

This project is a fork of django-pyodbc_ and so most credit goes to the folks who worked on that:

* Ramiro Morales `<http://djangopeople.net/ramiro/>`_
* Filip Wasilewski (http://code.djangoproject.com/ticket/5246)
* Wei guangjing `<http://djangopeople.net/vcc/>`_
* mamcx (http://code.djangoproject.com/ticket/5062)

The Netezza modifications were made by `Marc Abramowitz`_ of BlueKai_ (marc at nospam bluekai dot nospam com).

.. _Marc Abramowitz: http://marc-abramowitz.com/
.. _django-pyodbc: http://code.google.com/p/django-pyodbc/
.. _BlueKai: http://bluekai.com/


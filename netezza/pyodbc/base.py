"""
Netezza database backend for Django.
"""
import types
import sys
import pyodbc

try:
    import pyodbc as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading pyodbc module: %s" % e)

from django.db.backends import BaseDatabaseWrapper, BaseDatabaseFeatures, BaseDatabaseValidation
from django.db.backends.signals import connection_created
from django.conf import settings
from django import VERSION as DjangoVersion
if DjangoVersion[:2] == (1, 2) :
    from django import get_version
    version_str = get_version()
    if 'SVN' in version_str and int(version_str.split('SVN-')[-1]) < 11952: # django trunk revision 11952 Added multiple database support.
        _DJANGO_VERSION = 11
    else:
        _DJANGO_VERSION = 12
elif DjangoVersion[:2] == (1, 1):
    _DJANGO_VERSION = 11
elif DjangoVersion[:2] == (1, 0):
    _DJANGO_VERSION = 10
elif DjangoVersion[0] == 1:
    _DJANGO_VERSION = 13
else:
    _DJANGO_VERSION = 9

from netezza.pyodbc.operations import DatabaseOperations
from netezza.pyodbc.client import DatabaseClient
from netezza.pyodbc.creation import DatabaseCreation
from netezza.pyodbc.introspection import DatabaseIntrospection
import os
import warnings

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError

class DatabaseFeatures(BaseDatabaseFeatures):
    pass

class DatabaseWrapper(BaseDatabaseWrapper):
    drv_name = None
    driver_needs_utf8 = None
    unicode_results = False
    datefirst = 7

    operators = {
        'exact': '= %s',
        'iexact': '= UPPER(%s)',
        'contains': 'LIKE %s',
        'icontains': 'LIKE UPPER(%s)',
        'regex': '~ %s',
        'iregex': '~* %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE %s',
        'endswith': 'LIKE %s',
        'istartswith': 'LIKE UPPER(%s)',
        'iendswith': 'LIKE UPPER(%s)',
    }


    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        if 'OPTIONS' in self.settings_dict:
            self.datefirst = self.settings_dict['OPTIONS'].get('datefirst', 7)
            self.unicode_results = self.settings_dict['OPTIONS'].get('unicode_results', False)

        self.features = DatabaseFeatures(None)
        self.ops = DatabaseOperations()
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        if _DJANGO_VERSION >= 12:
            self.validation = BaseDatabaseValidation(self)
        else:
            self.validation = BaseDatabaseValidation()

        self.connection = None

    def _cursor(self):
        new_conn = False
        settings_dict = self.settings_dict
        db_str, user_str, passwd_str, port_str = None, None, None, None
        if _DJANGO_VERSION >= 12:
            options = settings_dict['OPTIONS']
            if settings_dict['NAME']:
                db_str = settings_dict['NAME']
            if settings_dict['HOST']:
                host_str = settings_dict['HOST']
            else:
                host_str = 'localhost'
            if settings_dict['USER']:
                user_str = settings_dict['USER']
            if settings_dict['PASSWORD']:
                passwd_str = settings_dict['PASSWORD']
            if settings_dict['PORT']:
                port_str = settings_dict['PORT']
        else:
            options = settings_dict['DATABASE_OPTIONS']
            if settings_dict['DATABASE_NAME']:
                db_str = settings_dict['DATABASE_NAME']
            if settings_dict['DATABASE_HOST']:
                host_str = settings_dict['DATABASE_HOST']
            else:
                host_str = 'localhost'
            if settings_dict['DATABASE_USER']:
                user_str = settings_dict['DATABASE_USER']
            if settings_dict['DATABASE_PASSWORD']:
                passwd_str = settings_dict['DATABASE_PASSWORD']
            if settings_dict['DATABASE_PORT']:
                port_str = settings_dict['DATABASE_PORT']
        if self.connection is None:
            new_conn = True

            cstr_parts = []

            if 'dsn' in options:
                cstr_parts.append('DSN=%s' % options['dsn'])
            else:
                if not db_str:
                    from django.core.exceptions import ImproperlyConfigured
                    raise ImproperlyConfigured('You need to specify NAME in your Django settings file.')

                cstr_parts.append('DATABASE=%s' % db_str)

            if 'extra_params' in options:
                cstr_parts.append(options['extra_params'])

            connstr = ';'.join(cstr_parts)
            autocommit = options.get('autocommit', True)
            if self.unicode_results:
                self.connection = Database.connect(connstr, \
                        autocommit=autocommit, \
                        unicode_results='True')
            else:
                self.connection = Database.connect(connstr, \
                        autocommit=autocommit, ansi=True)
            connection_created.send(sender=self.__class__)

        cursor = self.connection.cursor()
        set_tz = settings_dict.get('TIME_ZONE')
        if new_conn:
            if set_tz:
                cursor.execute("SET TIME ZONE '%s'" % set_tz)
            self.driver_needs_utf8 = True
        return CursorWrapper(cursor, self.driver_needs_utf8)


class CursorWrapper(object):
    """
    A wrapper around the pyodbc's cursor that takes in account a) some pyodbc
    DB-API 2.0 implementation and b) some common ODBC driver particularities.
    """
    def __init__(self, cursor, driver_needs_utf8):
        self.cursor = cursor
        self.driver_needs_utf8 = driver_needs_utf8
        self.last_sql = ''
        self.last_params = ()

    def format_sql(self, sql, n_params=None):
        if self.driver_needs_utf8 and isinstance(sql, unicode):
            # FreeTDS (and other ODBC drivers?) doesn't support Unicode
            # yet, so we need to encode the SQL clause itself in utf-8
            sql = sql.encode('utf-8')
        # pyodbc uses '?' instead of '%s' as parameter placeholder.
        if n_params is not None:
            sql = sql % tuple('?' * n_params)
        else:
            if '%s' in sql:
                sql = sql.replace('%s', '?')
        return sql

    def format_params(self, params):
        fp = []
        for p in params:
            if isinstance(p, unicode):
                if self.driver_needs_utf8:
                    # FreeTDS (and other ODBC drivers?) doesn't support Unicode
                    # yet, so we need to encode parameters in utf-8
                    fp.append(p.encode('utf-8'))
                else:
                    fp.append(p)
            elif isinstance(p, str):
                if self.driver_needs_utf8:
                    # TODO: use system encoding when calling decode()?
                    fp.append(p.decode('utf-8').encode('utf-8'))
                else:
                    fp.append(p)
            else:
                fp.append(p)
        return tuple(fp)

    def fix_none(self, sql, params):
        '''
        format Nones to 'NULL' in order to bypass the UnixODBC exception,
        when None is in parameters
        '''
        if len(params) < 1 or not None in params:
            return sql, params
        sql_parts = sql.split('?')
        new_sql = sql_parts[0]
        new_params = []
        for i, param in enumerate(params):
            if param is None:
                new_sql = '%sNULL%s' % (new_sql, sql_parts[i + 1])
            else:
                new_params.append(param)
                new_sql = '%s?%s' % (new_sql, sql_parts[i + 1])
        return new_sql, new_params

    def execute(self, sql, params=()):
        self.last_params = params
        self.last_sql = sql

        sql = self.format_sql(sql, len(params))
        params = self.format_params(params)
        sql, params = self.fix_none(sql, params)

        r = self.cursor.execute(sql, params)
        # self.cursor.connection.commit()
        return r

    def executemany(self, sql, params_list):
        sql = self.format_sql(sql)
        # pyodbc's cursor.executemany() doesn't support an empty param_list
        if not params_list:
            if '?' in sql:
                return
        else:
            raw_pll = params_list
            params_list = [self.format_params(p) for p in raw_pll]
        return self.cursor.executemany(sql, params_list)

    def format_results(self, rows):
        """
        Decode data coming from the database if needed and convert rows to tuples
        (pyodbc Rows are not sliceable).
        """
        if not self.driver_needs_utf8:
            return tuple(rows)
        # FreeTDS (and other ODBC drivers?) doesn't support Unicode
        # yet, so we need to decode utf-8 data coming from the DB
        fr = []
        for row in rows:
            if isinstance(row, types.StringType):
                fr.append(row.decode('utf-8'))
            else:
                fr.append(row)
        return tuple(fr)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is not None:
            return self.format_results(row)
        return []

    def fetchmany(self, chunk):
        return [self.format_results(row) for row in self.cursor.fetchmany(chunk)]

    def fetchall(self):
        return [self.format_results(row) for row in self.cursor.fetchall()]

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

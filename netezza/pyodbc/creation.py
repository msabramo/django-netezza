from django.db.backends.creation import BaseDatabaseCreation, \
    TEST_DATABASE_PREFIX
import base64
from django.utils.hashcompat import md5_constructor
import random
import sys

class DataTypesWrapper(dict):
    def __getitem__(self, item):
        if item in ('PositiveIntegerField', 'PositiveSmallIntegerField'):
            # The check name must be unique for the database. Add a random
            # component so the regresion tests don't complain about duplicate names
            fldtype = {'PositiveIntegerField': 'int', 'PositiveSmallIntegerField': 'smallint'}[item]
            rnd_hash = md5_constructor(str(random.random())).hexdigest()
            unique = base64.b64encode(rnd_hash, '__')[:6]
            return '%(fldtype)s CONSTRAINT [CK_%(fldtype)s_pos_%(unique)s_%%(column)s] CHECK ([%%(column)s] >= 0)' % locals()
        return super(DataTypesWrapper, self).__getitem__(item)

class DatabaseCreation(BaseDatabaseCreation):
    # This dictionary maps Field objects to their associated Netezza SQL column
    # types, as strings. Column-type strings can contain format strings; they'll
    # be interpolated against the values of Field.__dict__ before being output.
    # If a column type is set to None, it won't be included in the output.
    #
    # Any format strings starting with "qn_" are quoted before being used in the
    # output (the "qn_" prefix is stripped before the lookup is performed.

    data_types = {
        'AutoField':         'IDENTITY (1, 1, 1)',
        'BooleanField':      'BOOLEAN',
        'CharField':         'VARCHAR(%(max_length)s)',
        'CommaSeparatedIntegerField': 'VARCHAR(%(max_length)s)',
        'DateField':         'DATE',
        'DateTimeField':     'DATETIME',
#        'DecimalField':      'numeric(%(max_digits)s, %(decimal_places)s)',
        'DecimalField':      'DECIMAL',
        'FileField':         'VARCHAR(%(max_length)s)',
        'FilePathField':     'VARCHAR(%(max_length)s)',
        'FloatField':        'FLOAT',
        'IntegerField':      'INTEGER',
        'IPAddressField':    'VARCHAR(15)',
        'NullBooleanField':  'BOOLEAN',
        'OneToOneField':     'INTEGER',
        #'PositiveIntegerField': 'integer CONSTRAINT [CK_int_pos_%(column)s] CHECK ([%(column)s] >= 0)',
        #'PositiveSmallIntegerField': 'smallint CONSTRAINT [CK_smallint_pos_%(column)s] CHECK ([%(column)s] >= 0)',
        'PositiveIntegerField': 'INTEGER',
        'PositiveSmallIntegerField': 'SMALLINT',
        'SlugField':         'VARCHAR(%(max_length)s)',
        'SmallIntegerField': 'SMALLINT',
        'TextField':         'VARCHAR(65000)',
        'TimeField':         'TIME',
    }

    def _create_test_db(self, verbosity, autoclobber):
        "Internal implementation - creates the test db tables."
        suffix = self.sql_table_creation_suffix()

        if self.connection.settings_dict['TEST_NAME']:
            test_database_name = self.connection.settings_dict['TEST_NAME']
        else:
            test_database_name = TEST_DATABASE_PREFIX + self.connection.settings_dict['NAME']

        qn = self.connection.ops.quote_name

        # Create the test database and connect to it. We need to autocommit
        # if the database supports it because PostgreSQL doesn't allow
        # CREATE/DROP SCHEMA statements within transactions.
        cursor = self.connection.cursor()
        self.set_autocommit()
        try:
            cursor.execute("CREATE SCHEMA %s %s" % (qn(test_database_name), suffix))
        except Exception, e:
            sys.stderr.write("Got an error creating the test database: %s\n" % e)
            if not autoclobber:
                confirm = raw_input("Type 'yes' if you would like to try deleting the test database '%s', or 'no' to cancel: " % test_database_name)
            if autoclobber or confirm == 'yes':
                try:
                    if verbosity >= 1:
                        print "Destroying old test database..."
                    cursor.execute("DROP SCHEMA %s" % qn(test_database_name))
                    if verbosity >= 1:
                        print "Creating test database..."
                    cursor.execute("CREATE SCHEMA %s %s" % (qn(test_database_name), suffix))
                except Exception, e:
                    sys.stderr.write("Got an error recreating the test database: %s\n" % e)
                    sys.exit(2)
            else:
                print "Tests cancelled."
                sys.exit(1)

        return test_database_name

    def _destroy_test_db(self, test_database_name, verbosity):
        "Internal implementation - remove the test db tables."
        cursor = self.connection.cursor()
        self.set_autocommit()
        #time.sleep(1) # To avoid "database is being accessed by other users" errors.
        cursor.execute("ALTER DATABASE %s SET SINGLE_USER WITH ROLLBACK IMMEDIATE " % \
                self.connection.ops.quote_name(test_database_name))
        cursor.execute("DROP SCHEMA %s" % \
                self.connection.ops.quote_name(test_database_name))
        self.connection.close()

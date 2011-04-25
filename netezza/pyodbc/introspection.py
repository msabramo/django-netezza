from django.db.backends import BaseDatabaseIntrospection
import pyodbc as Database
import types
import datetime
import decimal

class DatabaseIntrospection(BaseDatabaseIntrospection):
    # Map type codes to Django Field types.
    data_types_reverse = {
        types.StringType:               'TextField',
        types.UnicodeType:              'TextField',
        types.LongType:                 'IntegerField',
        types.IntType:                  'IntegerField',
        types.BooleanType:              'BooleanField',
        types.FloatType:                'FloatField',
        datetime.datetime:              'DateTimeField',
        datetime.date:                  'DateField',
        datetime.time:                  'TimeField',
        decimal.Decimal:                'DecimalField',
    }

    def get_table_list(self, cursor):
        """
        Returns a list of table names in the current database.
        """
#        db = cursor.db.alias
#        if db == 'default':
        db = 'public'
        cursor.execute("""
            SELECT distinct objname
            FROM _v_obj_relation
            WHERE objclass IN (4905,4906,4908,4907,4909,4940,4911,4913,4953);""")
        return [row[0] for row in cursor.fetchall()]


    def get_table_description(self, cursor, table_name, identity_check=True):
        "Returns a description of the table, with the DB-API cursor.description interface."
        cursor.execute("SELECT * FROM %s LIMIT 1" % self.connection.ops.quote_name(table_name))
        return cursor.description

    def _name_to_index(self, cursor, table_name):
        """
        Returns a dictionary of {field_name: field_index} for the given table.
        Indexes are 0-based.
        """
        return dict([(d[0], i) for i, d in enumerate(self.get_table_description(cursor, table_name, identity_check=False))])

    def get_relations(self, cursor, table_name):
        return []
    
        """
        Returns a dictionary of {field_index: (field_index_other_table, other_table)}
        representing all relationships to the given table. Indexes are 0-based.
        """
        cursor.execute("""
SELECT fk.ORDINAL_POSITION, col.ORDINAL_POSITION, fk.REFERENCE_TABLE_NAME
FROM FOREIGN_KEYS fk
INNER JOIN COLUMNS col on fk.REFERENCE_COLUMN_NAME = col.COLUMN_NAME
                       and fk.REFERENCE_TABLE_NAME = col.TABLE_NAME
WHERE fk.TABLE_NAME = %s
""", [table_name])
        relations = {}
        for row in cursor.fetchall():
            # row[0] and row[1] are like "{2}", so strip the curly braces.
            relations[row[0]] = (row[1], row[2])
        return relations

    def get_indexes(self, cursor, table_name):
        return []
    
        """
        Returns a dictionary of fieldname -> infodict for the given table,
        where each infodict is in the format:
            {'primary_key': boolean representing whether it's the primary key,
             'unique': boolean representing whether it's a unique index,
             'db_index': boolean representing whether it's a non-unique index}
        """
        cursor.execute("""
SELECT col.COLUMN_NAME,pk.CONSTRAINT_TYPE
FROM V_CATALOG.COLUMNS col
left join V_CATALOG.PRIMARY_KEYS pk
  ON col.TABLE_NAME = pk.TABLE_NAME AND col.COLUMN_NAME = pk.COLUMN_NAME
WHERE col.TABLE_NAME = %s""", [table_name])
        indexes = {}
        for row in cursor.fetchall():
            indexes[row[0]] = {'primary_key': row[1] == 'p', 'unique': False}
        return indexes

    def get_field_type(self, data_type, description):
        """Hook for a database backend to use the cursor description to
        match a Django field type to a database column.

        For Oracle, the column data_type on its own is insufficient to
        distinguish between a FloatField and IntegerField, for example."""
        try:
            return self.data_types_reverse[data_type]
        except:
            print '*' * 10,'DEBUG add the type', data_type, 'to introspection.py'
            raise

"""
The DBObject base class

ben@adida.net
"""

from base import utils,DB

import simplejson
import datetime

##
## WOOHOO, utf-8 now handled correctly by psycopg2
##

class DBObject(object):

    def __init__(self):
        pass
        
    def _prepare_sql_values(self):
        """
        prepares the values to insert.
        By overriding prepare_sql_values, a child class can format a few things.
        """
        values = self.__dict__.copy()
        
        self.prepare_sql_values(values)
        return values

    def prepare_sql_values(self, values):
        pass

    def all_fields_sql(cls, with_table_prefix=True, field_substitution=False):
        fields = cls.FIELDS

        # substitute
        if field_substitution:
            fields = [cls._one_field_sql(f) for f in fields]

        if with_table_prefix:
            fields = [cls.TABLE_NAME + "." + f for f in fields]

        return ",".join(fields)
    all_fields_sql = classmethod(all_fields_sql)

    def _prepare_object_values(self, row):
        """
        prepares the values after they come back from SQL
        to be set up correctly as object values.
        """
        prepared_row = dict()
        prepared_row.update(row)
        self.prepare_object_values(prepared_row)
        return prepared_row

    def prepare_object_values(self, values):
        pass

    def _one_field_sql(cls, field):
        """
        manipulate a single field at select time
        """
        return field
    _one_field_sql = classmethod(_one_field_sql)

    @classmethod
    def _select_sql_statement(cls, keys = None):
        sql = "select "
        sql += cls.all_fields_sql(field_substitution=True)
        sql += " from " + cls.TABLE_NAME

        if keys:
            extra_sql = " and ".join(["%s = %s" % (key_name, DB.dbstr(key_value)) for key_name,key_value in keys.iteritems()])
            if extra_sql != "":
                sql += " where " + extra_sql

        return sql
        
    def select(self, keys):
        if not keys or len(keys) == 0:
            keys[self.PRIMARY_KEY] = self.__attr__[self.PRIMARY_KEY]

        sql = self._select_sql_statement(keys)

        row = DB.onerow(sql)
        if row == None:
            return False

        self._load_from_row(row)
        return True

    def selectById(cls, key_value):
        return cls.selectByKey(key_name = cls.PRIMARY_KEY, key_value = key_value)
    selectById = classmethod(selectById)

    @classmethod
    def selectByKey(cls, key_name, key_value):
        obj = cls()
        if obj.select(keys={key_name:key_value}):
            return obj
        else:
            return None
    
    @classmethod
    def selectByKeys(cls, keys):
        obj = cls()
        if obj.select(keys):
            return obj
        else:
            return None

    @classmethod
    def selectAll(cls, order_by = None, offset = None, limit = None):
        sql = "select "
        sql += cls.all_fields_sql(field_substitution=True)
        sql += " from " + cls.TABLE_NAME

        if order_by != None:
            sql += " order by " + order_by

        if offset:
            sql += " offset " + offset

            if limit:
                sql += " limit " + limit

        rows = DB.multirow(sql)

        if rows == None:
            return None

        return cls.multirow_to_array(rows)

    @classmethod
    def selectAllByKey(cls, key_name, key_value, order_by = None, offset = None, limit = None):
        keys = dict()
        keys[key_name] = key_value
        return cls.selectAllByKeys(keys, order_by, offset, limit)
        
    @classmethod
    def selectAllByKeys(cls, keys, order_by = None, offset = None, limit = None):
        for key_name in keys.keys():
            if key_name not in cls.FIELDS:
                return None

        sql = "select "
        sql += cls.all_fields_sql(field_substitution=True)
        sql += " from " + cls.TABLE_NAME
        sql += " where "
        
        sql_clauses = []
        for k,v in keys.items():        
            # null or not null
            if v:
                sql_value = " = " + str(DB.dbstr(v))
            else:
                sql_value = " is NULL "
            
            sql_clauses.append(k + sql_value)

        sql += " and ".join(sql_clauses)

        if order_by:
            sql += " order by " + order_by

        # add offset and limit
        if offset:
            sql += " offset " + offset

            if limit:
                sql += " limit " + limit

        rows = DB.multirow(sql)

        if rows == None:
            return None

        return cls.multirow_to_array(rows)    

    def _load_from_row(self, row, extra_fields=[]):

        prepared_row = self._prepare_object_values(row)
        
        for field in self.FIELDS:
            self.__dict__[field] = prepared_row[field]

        for field in extra_fields:
            self.__dict__[field] = prepared_row[field]

    def insert(self, generate_new_pkey= True):
        """
        Insert a new object, but only if it hasn't been inserted yet
        """
        if generate_new_pkey:
            if self.PRIMARY_KEY in self.__dict__:
                if self.__dict__[self.PRIMARY_KEY] != None:
                    raise Exception('primary key already set')

        sql = "insert into " + self.TABLE_NAME
        sql += "(" + self.all_fields_sql(with_table_prefix=False) + ") "

        if generate_new_pkey:
            self.__dict__[self.PRIMARY_KEY] = int(DB.oneval("select nextval('" + self.SEQ_NAME + "')"))

        sql += "values (" + ",".join([self._sql_insert_value(f) for f in self.FIELDS]) + ")"

        DB.perform(sql, extra_vars = self._prepare_sql_values())

    def _sql_insert_value(self, field_name):
        """
        Prepare the insert SQL for a field name, remembering that
        the field value may be a string substitution piece for Python
        """
        return "%(" + field_name + ")s"

    def update(self):
        """
        Update an object
        """
        sql = "update " + self.TABLE_NAME
        sql += " set "

        field_statements = []
        for field in self.FIELDS:
            try:
                if field == self.PRIMARY_KEY: continue
            except:
                continue
            field_statements.append(field + " = " + self._sql_insert_value(field))

        sql += ",".join(field_statements)

        sql += " where " + self.PRIMARY_KEY + " = %(" + self.PRIMARY_KEY + ")s"

        DB.perform(sql, extra_vars = self._prepare_sql_values())

    def delete(self):
        """
        Delete an object
        """
        sql = "delete from " + self.TABLE_NAME
        sql += " where " + self.PRIMARY_KEY + " = %(pkval)s"

        pkval = self.__dict__[self.PRIMARY_KEY]
        DB.perform(sql)

    @classmethod
    def multirow_to_array(cls, multirow, extra_fields=[]):
        objects = []

        if multirow == None:
            return objects

        for row in multirow:
            one_object = cls()
            one_object._load_from_row(row, extra_fields)
            objects.append(one_object)

        return objects
    
    def toJSONDict(self):
        # a helper recursive procedure to navigate down the items
        # even if they don't have a toJSONDict() method
        def toJSONRecurse(item):
            if type(item) == int or type(item) == bool or hasattr(item, 'encode') or not item:
                return item

            if hasattr(item,'toJSONDict'):
                return item.toJSONDict()
            
            if type(item) == list:
                return [toJSONRecurse(el) for el in item]
                
            if type(item) == dict:
                new_dict = dict()
                for k in item.keys():
                    new_dict[k] = toJSONRecurse(item[k])
                return new_dict

            return str(item)
            
        # limit the fields to just JSON_FIELDS if it exists
        json_dict = dict()
        if hasattr(self.__class__,'JSON_FIELDS'):
            keys = self.__class__.JSON_FIELDS
        else:
            keys = self.__dict__.keys()
        
        # go through the keys and recurse down each one
        for f in keys:
            if not self.__dict__.has_key(f):
                continue
            
            json_dict[f] = toJSONRecurse(self.__dict__[f])

        return json_dict
        
    def toJSON(self):
        return simplejson.dumps(self.toJSONDict())
#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import datetime
import random
import unittest

import dateutil.tz
import MySQLdb
import MySQLdb.cursors
import _mysql_exceptions

import basetranslate
import config


class ShortDBConn(object):
    """Connection to Short database.

    Args:
        data_table_name: name of table with ID mappings.
        info_table_name: name of table with database settings (i.e. the base
            reprentation characters).
        host: MySQL hostname      (default: localhost)
        user: MySQL username      (default: short)
        db:   MySQL database name (default: short)
        **kwargs: passed to MySQLdb.connect(), except cursorclass attribute,
                  which is hardcoded to MySQLdb.cursors.DictCursor.

    Usage:
        with ShortDBConn(...) as myconn:
            ...

    Raises:
        _mysql_exceptions.OperationalError on failed MySQL login.
    """
    def __init__(self, host='localhost', user='short', db='short',
                 data_table_name='translation_table',
                 info_table_name='base_info', **kwargs):
        self._data_table_name = data_table_name
        self._info_table_name = info_table_name
        kwargs['cursorclass'] = MySQLdb.cursors.DictCursor
        self.conn = MySQLdb.connect(host=host, user=user, db=db, **kwargs)
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.cursor.close()

    @property
    def base_chars(self):
        """Base character representation."""
        try:
            return self._base_chars
        except AttributeError:
            query = 'SELECT base_chars FROM {} LIMIT 1'.format(
                    self._info_table_name)
            self.cursor.execute(query)
            self._base_chars = self.cursor.fetchone()['base_chars']
            return self._base_chars


    def add(self, long_url):
        """Add new URL mapper.

        Args:
            Long URL.

        Returns:
            base representation of column in database for corresponding row.
        """
        if not long_url.startswith(('http://', 'https://')):
            long_url = 'http://' + long_url

        query = 'INSERT INTO {} (long_url, created) VALUES(%s, now())'.format(
            self._data_table_name)
        self.cursor.execute(query, (long_url))
        self.conn.commit()
        # Capture this before the self.base_chars call, since that reuses the
        # cursor for fetching the base which resets self.cursor.lastrowid.
        new_id = self.cursor.lastrowid
        return basetranslate.Translation(self.base_chars).int_to_base(new_id)


class ShortDBEntry(basetranslate.BaseItem):
    """Entry in Short database with properties."""
    def __init__(self, conn, base_id, data_table_name='translation_table'):
        self._data_table_name = data_table_name
        self.conn = conn.conn
        self.cursor = conn.cursor

        super(ShortDBEntry, self).__init__(conn.base_chars, base_id)

        query = ('SELECT long_url, last_accessed, created, access_counter FROM '
            '{} WHERE id=%s'.format(self._data_table_name))
        self.cursor.execute(query, (self.int_id))
        result = self.cursor.fetchone()

        if result is None:
            raise IndexError('Entry {} in the custom base (int: {}) does not '
                'have a corresponding database entry.'.format(self.base_id,
                                                              self.int_id))

        self._long_url = result['long_url']

        # Assume that the items were stored with the same server timezone
        # settings that they are retrieved with. MySQL has no apparent way of
        # storing timezone info with time objects.
        #
        # This also handles DST correctly.
        tz = dateutil.tz.tzlocal()
        try:
            self._last_accessed = result['last_accessed'].replace(tzinfo=tz)
        except AttributeError:
            self._last_accessed = None
        self._created = result['created'].replace(tzinfo=tz)

        self._access_counter = int(result['access_counter'])

    @property
    def long_url(self):
        return self._long_url

    @property
    def last_accessed(self):
        """Timezone aware datetime.datetime object of last accessed time.
        Returns None if never accessed."""
        return self._last_accessed

    @property
    def created(self):
        """Timezone aware datetime.datetime object of creation time."""
        return self._created

    @property
    def access_counter(self):
        return self._access_counter

    def increment(self):
        """Increment access counter by 1."""
        query = ('UPDATE {} set access_counter=(access_counter+1) WHERE id=%s'
                .format(self._data_table_name))
        self.cursor.execute(query, (self.int_id))
        self.conn.commit()
        self._access_counter += 1


class TestSequence(unittest.TestCase):
    def setUp(self):
        c = config.ConfigItems(config_file='../shortweb.test.config')

        self.host = c.dbargs['host']
        self.user = c.dbargs['user']
        self.passwd = c.dbargs['passwd']
        self.db = c.dbargs['db']
        self.data_table_name = c.dbargs['data_table_name']
        self.base_id_with_no_corresponding_db_entry = \
                c.dbargs['base_id_with_no_corresponding_db_entry']
        self.long_url = c.dbargs['long_url']
        self.base_id = c.dbargs['base_id']


    def test_short_db_entry_private_variables(self):
        """Shouldn't be able to set private variables in ShortDBEntry."""
        with ShortDBConn(passwd=self.passwd,
                data_table_name=self.data_table_name) as short_db_conn:
            short_db_entry = ShortDBEntry(short_db_conn, self.base_id,
                                          data_table_name=self.data_table_name)

            with self.assertRaises(AttributeError):
                short_db_entry.long_url = 'test'
            with self.assertRaises(AttributeError):
                short_db_entry.last_accessed = 'test'
            with self.assertRaises(AttributeError):
                short_db_entry.created = 'test'
            with self.assertRaises(AttributeError):
                short_db_entry.access_counter = 'test'

    def test_short_db_entry_db_lookups(self):
        """Test DB lookups in ShortDBEntry."""
        with ShortDBConn(passwd=self.passwd,
                data_table_name=self.data_table_name) as short_db_conn:
            short_db_entry = ShortDBEntry(short_db_conn, self.base_id,
                                          data_table_name=self.data_table_name)

            self.assertEqual(short_db_entry.long_url, self.long_url)
            self.assertIsNone(short_db_entry.last_accessed, datetime.datetime)
            self.assertIsInstance(short_db_entry.created, datetime.datetime)
            self.assertIsInstance(short_db_entry.access_counter, int)

            with self.assertRaises(IndexError):
                ShortDBEntry(short_db_conn,
                             self.base_id_with_no_corresponding_db_entry,
                             data_table_name=self.data_table_name)

    def test_short_db_conn_private_variables(self):
        """Shouldn't be able to set private variables in ShortDBConn."""
        with ShortDBConn(passwd=self.passwd,
                data_table_name=self.data_table_name) as short_db_conn:
            with self.assertRaises(AttributeError):
                short_db_conn.base_chars = 'test'

    def test_short_db_conn_add_and_increment(self):
        """Add URL with ShortDBConn, instantiate with ShortDBEntry, check
        increment function."""
        with ShortDBConn(passwd=self.passwd,
                data_table_name=self.data_table_name) as short_db_conn:
            test_url = 'example.com/?rand='+str(random.random())
            self.new_base_id = short_db_conn.add(test_url)
            test_args = (short_db_conn, self.new_base_id)
            test_kwargs = {'data_table_name': self.data_table_name}
            test_item = ShortDBEntry(*test_args, **test_kwargs)
            self.new_int_id = test_item.int_id
            self.assertEqual(test_item.long_url, 'http://' + test_url)

            # Save AC, increment, check new access_counter, reload object,
            # check that it went up by 1 also in the DB.
            pre_access_counter = test_item.access_counter
            test_item.increment()
            self.assertEqual(pre_access_counter, test_item.access_counter-1)
            test_item = ShortDBEntry(*test_args, **test_kwargs)
            self.assertIsInstance(test_item.last_accessed, datetime.datetime)
            self.assertEqual(pre_access_counter, test_item.access_counter-1)

    def test_short_db_conn_failed_login(self):
        """Failed login should raise _mysql_exceptions.OperationalError."""
        with self.assertRaises(_mysql_exceptions.OperationalError):
            ShortDBConn(passwd='invalid')

    def tearDown(self):
        try:
            self.new_base_id
        except AttributeError:
            pass
        else:
            with ShortDBConn(passwd=self.passwd,
                    data_table_name=self.data_table_name) as short_db_conn:
                conn = short_db_conn.conn
                cursor = conn.cursor()
                query = 'DELETE FROM {} WHERE id=%s'.format(
                        self.data_table_name)
                cursor.execute(query, self.new_int_id)
                conn.commit()

                # Call a stored procedure to reset auto increment value to
                # smallest available ID. Procedure created via:
                #
                #     DROP PROCEDURE IF EXISTS reset_test_autoincrement;
                #     DELIMITER $$
                #     CREATE PROCEDURE reset_test_autoincrement()
                #     BEGIN
                #       SELECT @maxaddone:=max(id)+1
                #           FROM test_translation_table;
                #       SET @query = CONCAT('ALTER TABLE test_translation_table
                #                            AUTO_INCREMENT=', @maxaddone);
                #       PREPARE stmt FROM @query;
                #       EXECUTE stmt;
                #       DEALLOCATE PREPARE stmt;
                #     END $$
                #     DELIMITER ;
                #
                # CONCAT() is used since variables can't be bound in ALTER
                # TABLE statements. This was not the first time this has wasted
                # time for me. Some say that it is possible, and some even say
                # that the documentation states that it is possible, but I for
                # sure cannot get it to work in MySQL 5.5.30.
                #
                # At first I tried to do things via PhpMyAdmin, but that has
                # its own share of quirks regarding stored procedures. The
                # DELIMITER statement should not be called in the code input
                # fields, but a special option should be set instead. To add to
                # this: for some infinitely strange reason, I could store
                # procedures through PMA that worked _when called from within
                # PMA_ with `CALL procedure`, but they did _not_ work when
                # called from other connections. !"#¤%&/ unbelievable.
                #
                # This could also have been done directly here in Python, but I
                # wanted to experiment with the above way instead. For
                # posterity: 
                #
                #     query = (
                #         'SELECT @maxaddone:=max(id)+1 FROM {};'.format(
                #                 self.data_table_name),
                #         'SET @query = CONCAT("ALTER TABLE {} '
                #                 'AUTO_INCREMENT=", @maxaddone);'.format(
                #                         self.data_table_name),
                #         'PREPARE stmt FROM @query;',
                #         'EXECUTE stmt;',
                #         'DEALLOCATE PREPARE stmt;')
                #     for i in query:
                #         cursor.execute(i)
                #
                cursor.callproc('reset_test_autoincrement')


def main():
    unittest.main()


if __name__ == '__main__':
    main()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import ConfigParser
import StringIO
import unittest


class ConfigItems(object):
    """Return configuration file values from sections "DB" and "Web" in a
    configuration file readable by ConfigParser.SafeConfigParser as defined in
    the documentation of the ConfigParser module.

    Args:
        config_file_descriptor: optional file descriptor.
        config_file: optional filename.

        One of those must be set. config_file_descriptor takes precedence if
        both are set.

    Returns:
        ConfigItems object.

    Raises:
        IOError if file not found.
        NoSectionError if config file is missing [DB] and/or [Web] sections.
    """
    def __init__(self, config_file_descriptor=None,
                 config_file='shortweb.config'):
        config = ConfigParser.SafeConfigParser()
        try:
            config.readfp(config_file_descriptor)
        except AttributeError:
            with open(config_file) as f:
                config.readfp(f)

        self._dbargs = dict(config.items('DB'))
        self._webargs = dict(config.items('Web'))

    @property
    def dbargs(self):
        return self._dbargs

    @property
    def webargs(self):
        return self._webargs


class TestSequence(unittest.TestCase):
    def setUp(self):
        self.fields = {
                'host':'localhost',
                'user': 'short',
                'passwd': 'shortpassword',
                'db': 'short',
                'base_url': 'http://example.com/s/',
                'title': 'Test suite title',
                'h1': 'Test suite h1'}

    def test_configitems_data_integrity(self):
        """Read back values should be identical to input."""
        config_contents = (
                '[DB]\n'
                'host = {host}\n'
                'user = {user}\n'
                'passwd = {passwd}\n'
                'db = {db}\n'
                '\n'
                '[Web]\n'
                'base_url = {base_url}\n'
                'title = {title}\n'
                'h1 = {h1}').format(**self.fields)

        testfile = StringIO.StringIO(config_contents)
        c = ConfigItems(config_file_descriptor=testfile)

        self.assertEqual(c.dbargs['host'], self.fields['host'])
        self.assertEqual(c.dbargs['user'], self.fields['user'])
        self.assertEqual(c.dbargs['passwd'], self.fields['passwd'])
        self.assertEqual(c.dbargs['db'], self.fields['db'])
        self.assertEqual(c.webargs['base_url'], self.fields['base_url'])
        self.assertEqual(c.webargs['title'], self.fields['title'])

    def test_configitems_sections_exist(self):
        """Lack of [DB] and/or [Web] sections should raise
        ConfigParser.NoSectionError."""
        config_contents_no_db = (
                '[Web]\n'
                'base_url = {base_url}\n'
                'title = {title}\n'
                'h1 = {h1}').format(**self.fields)

        config_contents_no_web = (
                '[DB]\n'
                'host = {host}\n'
                'user = {user}\n'
                'passwd = {passwd}\n'
                'db = {db}\n').format(**self.fields)


        with self.assertRaises(ConfigParser.NoSectionError):
            testfile = StringIO.StringIO(config_contents_no_db)
            ConfigItems(config_file_descriptor=testfile)

        with self.assertRaises(ConfigParser.NoSectionError):
            testfile = StringIO.StringIO(config_contents_no_web)
            ConfigItems(config_file_descriptor=testfile)

    def test_configuration_no_empty_values(self):
        """Empty values should not be allowed and raise
        ConfigParser.ParserError."""
        config_contents_empty_value = (
                '[DB]\n'
                'host\n'
                '\n'
                '[Web]\n'
                'base_url = {base_url}\n'
                'title = {title}\n'
                'h1 = {h1}').format(**self.fields)

        with self.assertRaises(ConfigParser.ParsingError):
            testfile = StringIO.StringIO(config_contents_empty_value)
            ConfigItems(config_file_descriptor=testfile)

    def test_configitems_non_existent_file(self):
        """Non-existent filename should raise IOError."""
        with self.assertRaises(IOError):
            ConfigItems(config_file='/bananarama')

    def test_configitems_interpolation(self):
        """Ensure implementation of ConfigParser style %()s interpolation."""
        config_contents_interpolation = (
                '[DB]\n'
                'host = {host}\n'
                'user = {user}\n'
                'passwd = {passwd}\n'
                'db = {db}\n'
                '\n'
                '[Web]\n'
                'domain = {domain}\n'
                'base_url = %(domain)s/s/\n'
                'title = %(domain)s title\n'
                'h1 = %(title)s in body\n').format(domain='example.com',
                                                   **self.fields)

        testfile = StringIO.StringIO(config_contents_interpolation)
        c = ConfigItems(config_file_descriptor=testfile)

        self.assertEqual(c.webargs['base_url'], 'example.com/s/')
        self.assertEqual(c.webargs['title'], 'example.com title')
        self.assertEqual(c.webargs['h1'], 'example.com title in body')


def main():
    unittest.main()


if __name__ == '__main__':
    main()

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import unittest

import cgi

import basetranslate
import config


class HtmlPrinter(object):
    """Print headers and HTML."""
    def __init__(self, base_url='http://example.com/', title='Example title',
                 **kwargs):
        self._base_url = base_url
        self._title = title

    @property
    def base_url(self):
        return self._base_url

    @property
    def title(self):
        return self._title

    def _content_header(self):
        """Print 'Content-type' CGI header."""
        print 'Content-Type: text/html; charset=utf-8'
        print

    def _html_starter(self):
        """Print boilerplate HTML preamble."""
        print ('<!DOCTYPE html>\n'
               '<meta charset="utf-8">\n'
               '<title>{title}</title>\n').format(title=self.title)

    def _html_ender(self):
        """Print boilerplate HTML ending and exit."""
        sys.exit(0)

    def short_id_info(self, switem):
        """Print a table with information on the given item."""
        self._content_header()
        self._html_starter()

        if switem.last_accessed is None:
            last_accessed_markup = 'Not yet accessed'
        else:
            last_accessed_markup = ('<time datetime="{isodate}">{date}</time>'
                    '').format(isodate=switem.last_accessed.isoformat(),
                              date=switem.last_accessed)

        print ('<fieldset>\n'
               '  <legend>Link information</legend>\n'
               '\n'
               '  <table class="link_info">\n'
               '    <tr>\n'
               '      <th>ID\n'
               '      <td>{int_id} → {base_id}\n'
               '    <tr>\n'
               '      <th>Short URL\n'
               '      <td><a href="{base_url}{base_id}">{base_url}{base_id}'
               '</a>\n'
               '    <tr>\n'
               '      <th>Long URL\n'
               '      <td><a href="{long_url}">{long_url}</a>\n'
               '    <tr>\n'
               '      <th>Created\n'
               '      <td><time datetime="{created_iso}">{created}</time>\n'
               '    <tr>\n'
               '      <th>Last accessed\n'
               '      <td>{last_accessed_markup}'
               '</time>\n'
               '    <tr>\n'
               '      <th>Access counter\n'
               '      <td>{access_counter}\n'
               '  </table>\n'
               '</fieldset>').format(
                        int_id=switem.int_id,
                        base_id=switem.base_id,
                        base_url=cgi.escape(self.base_url, True),
                        long_url=cgi.escape(switem.long_url, True),
                        created_iso=switem.created.isoformat(),
                        created=switem.created,
                        last_accessed_markup=last_accessed_markup,
                        access_counter=switem.access_counter)
        self._html_ender()

    def short_url_to_id(self, dbconn, short_url):
        """Translate a complete short URL to its base representation."""
        base_id = short_url.lstrip(self.base_url).strip()

        if dbconn is not None:
            t = basetranslate.Translation(dbconn.base_chars)
            try:
                int_id = t.base_to_int(base_id)
            except ValueError:
                int_id = None
        else:
            int_id = None

        return (base_id, int_id)

    def short_id_not_found(self, dbconn, short_url):
        """Print error message saying that the link was not found in the
        database."""
        (base_id, int_id) = self.short_url_to_id(dbconn, short_url)

        self._content_header()
        self._html_starter()
        print ('<p class="not_found">Given short form does not exist in the '
                'database: {base_id} → ID {int_id}'.format(
                    base_id=base_id, int_id=int_id))
        self._html_ender()

    def invalid_short_id(self, dbconn, short_url):
        """Print error message saying that the link was of invalid form."""
        (base_id, int_id) = self.short_url_to_id(dbconn, short_url)

        self._content_header()
        self._html_starter()

        print ('<p class="invalid">Invalid short url: {short_url}.\n'
               '\n'
               '<p>Only the following characters are allowed in the short '
               'form: <pre>{base}</pre>').format(
                       short_url=self.base_url+base_id, base=dbconn.base_chars)

        self._html_ender()

    def new_url_form(self):
        """Print form for input of new database entry."""
        self._content_header()
        self._html_starter()
        print ('<form name="new" method="post">\n'
               '  <fieldset>\n'
               '    <legend>Add new short link</legend>\n'
               '\n'
               '    <table>\n'
               '      <tr>\n'
               '        <th>Link target\n'
               '        <td><input name="new_url" type="url" required '
               'size="100">\n'
               '      <tr>\n'
               '        <th>\n'
               '        <td><input name="submit_url" type="submit" '
               'value="Add">\n'
               '    </table>\n'
               '  </fieldset>\n'
               '</form>')
        self._html_ender()

    def reload(self, base_id):
        """Send CGI header to reload page to the information page of the short
        URL representation of the given ID."""
        print 'Location: {base_url}{base_id}+'.format(base_url=self.base_url,
                                                      base_id=base_id)
        print

    @staticmethod
    def redirect(long_url):
        """Send CGI header to redirect the user to the given long URL."""
        # <http://en.wikipedia.org/wiki/List_of_HTTP_status_codes>
        print 'Status: 301 Moved Permanently'
        print 'Location: {long_url}'.format(long_url=long_url)
        print


class TestSequence(unittest.TestCase):
    def setUp(self):
        c = config.ConfigItems(config_file='../shortweb.test.config')

        self.base_url = c.webargs['base_url']
        self.title = c.webargs['title']

        self.htmlprinter = HtmlPrinter(base_url=self.base_url,
                                       title=self.title)

    def test_htmlprinter_properties(self):
        """Properties should be set on initialization but not modifiable."""
        self.assertEqual(self.htmlprinter.base_url, self.base_url)
        self.assertEqual(self.htmlprinter.title, self.title)

        with self.assertRaises(AttributeError):
            self.htmlprinter.base_url = 'Test'
        with self.assertRaises(AttributeError):
            self.htmlprinter.title = 'Test'

    # TODO: Redirect sys.stdout to file descriptor via StringIO and make sure
    # print output corresponds to known values.


def main():
    unittest.main()


if __name__ == '__main__':
    main()

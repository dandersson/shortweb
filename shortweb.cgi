#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os

import cgi
import cgitb

import swlib.basetranslate
import swlib.dbinteraction
import swlib.printer
import swlib.config


def main():
    config = swlib.config.ConfigItems()
    dbconn = swlib.dbinteraction.ShortDBConn(**config.dbargs)
    htmlprinter = swlib.printer.HtmlPrinter(**config.webargs)

    cgitb.enable()
    form = cgi.FieldStorage()
    request_method = os.environ['REQUEST_METHOD']

    if request_method == 'POST' and 'new_url' in form:
        new_url = form.getfirst('new_url')
        item = swlib.basetranslate.BaseItem(dbconn.base_chars,
                                            dbconn.add(new_url))
        htmlprinter.reload(item.base_id)
    elif request_method == 'GET' and 'short' in form:
        short_url = cgi.escape(form.getfirst('short'))
        try:
            shortdbentry = swlib.dbinteraction.ShortDBEntry(dbconn, short_url)
        except IndexError:
            htmlprinter.short_id_not_found(dbconn, short_url)
        except ValueError:
            htmlprinter.invalid_short_id(dbconn, short_url)
        # Enable URL info to be shown by adding a trailing '+' to the URL;
        # after URL mangling, a trailing '+' becomes a trailing space.
        if short_url[-1] == ' ':
            htmlprinter.short_id_info(shortdbentry)
        else:
            shortdbentry.increment()
            htmlprinter.redirect(shortdbentry.long_url)
    else:
        htmlprinter.new_url_form()


if __name__ == '__main__':
    main()

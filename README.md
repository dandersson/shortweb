ShortWeb — a URL shortener written in Python
============================================
Long URLs are mapped to a short representation and available via a shorter URL.
Sample use cases:

* message length restricted forums (IRC, IM, etc.)
* ASCII representation of complicated URLs for technical reasons
* easily hand-writable URLs with low error rate on subsequent input.

Made from proof-of-concept and "would be fun to do some web programming in
Python" perspectives, and that is where it will most probably stay. I run it
locally for personal use only at the moment.

No styling has been done HTML-wise apart from semantic markup. It would be an
easy task to add, though.


Setup
-----
It is needed to set up

* the database structure
* the web server configuration
* the script configuration file to reflect above choices.


### Requirements
* A CGI enabled web server
* Python 2 (not archaic) with modules:
    * [MySQLdb](http://mysql-python.sourceforge.net/)
    * [dateutil](http://labix.org/python-dateutil)
* MySQL


### Configuration file
See `shortweb.example.config` in the base directory.


### Database
Default translation (short → long) table:

    CREATE TABLE IF NOT EXISTS `translation_table` (
      `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
      `long_url` varchar(2048) COLLATE utf8_unicode_ci NOT NULL,
      `last_accessed` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00'
          ON UPDATE CURRENT_TIMESTAMP,
      `created` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
      `access_counter` int(10) unsigned NOT NULL DEFAULT '0',
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

Default base representation table:

    CREATE TABLE IF NOT EXISTS `base_info` (
      `base_chars` varchar(53) COLLATE utf8_unicode_ci NOT NULL,
      PRIMARY KEY (`base_chars`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
    INSERT INTO `base_info` (`base_chars`) VALUES
    ('abcdefghijkmnopqrstuvwxyzACDEFGHJKLMNPQRTUVWXYZ234679');

Note that varchar(53) corresponds to the number of characters in the base.


### Base representation choice
The chosen base decides which characters are available for URL shortening.
Rules/guidelines:

* Make sure all characters are unique.
* Don't change base once the system is in place (this will destroy the
  short form mapping and invalidate previously generated URLs).
* Tabs, spaces and newlines are allowed for readability in code, but are
  stripped before use.
* Avoid `+/&?[]` and other characters that get mangled or otherwise special
  treatment in HTTP transmission. `+` is also used as a "magic value" as a URL
  with a trailing `+` shows the corresponding link info instead of redirecting.

The more available characters, the shorter the URLs become in general. _N_
allowed characters gives _N_^_M_ different entries for _M_ short ID characters.


### Sample Apache config
    #Enables <http://example.com/s/{shortid}> style links via mod_rewrite.
    <Directory /var/www>
        RewriteEngine on
        RewriteRule ^s/?([^/]*)/?$ /short?short=$1 [L]
    </Directory>

    #Keep the CGI directory out of the web root for security reasons.
    ScriptAlias /short "/path/to/the/script/shortweb.cgi"
    <Directory /path/to/the/script>
        Order allow,deny
        allow from all
    </Directory>


Unit tests
----------
If you are not interested in these, just skip this section.

### Configuration
Create a configuration file `shortweb.test.config` in the base directory. It
has the same form as the regular configuration file. Here is a sample to
illustrate some points:

    [DB]
    host = localhost
    user = short
    passwd = password
    db = short
    # Do the testing in a separate table. Not "really" needed, but good form in
    # case tests fail. Just copy the standard table to the one specified below.
    data_table_name = test_translation_table
    # Define a short form that is not supposed to have a corresponding
    # translation entry. The one below won't be assigned in my base until I
    # have 10^17 entries, so it's quite safe.
    base_id_with_no_corresponding_db_entry = bananarama
    # These two values are inserted into the table beforehand to test that
    # the modules return correct results.
    long_url = http://farside.ph.utexas.edu/teaching/jk1/lectures/node50.html
    # `c` in my base corresponds to `id`=2 in the test table.
    base_id = c

    [Web]
    base_url = http://example.com/s/
    title = Test suite title

One of the tests in swlib.dbinteraction uses a stored procedure in MySQL to
restore `AUTO_INCREMENT` on the test table after adding and removing test
entries. It can be commented or implemented in SQL in the test code via a
commented example, or the stored procedure can be added, also with instructions
in the file itself.


Upstream
--------
The project lives at <https://github.com/dandersson/shortweb>.

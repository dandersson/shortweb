#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import unittest


class Translation(object):
    """Translation table to arbitrary defined base."""
    def __init__(self, base):
        self.base = base

    @property
    def base(self):
        return self._base
    @base.setter
    def base(self, base):
        try:
            base = base.translate(None, ' \n\t')
        except AttributeError:
            raise TypeError('base should be represented by a string.')

        if not base:
            raise ValueError('base must not be an empty string')

        if not len(base) == len(set(base)):
            raise ValueError('base representation must not include repeated '
                    'characters.')

        self._base = base

    def int_to_base(self, int_id):
        """Translate an integer to its base representation."""
        if self.is_valid_int_id_form(int_id):
            out = []
            while int_id:
                (int_id, i) = divmod(int_id, len(self.base))
                out.append(self.base[i])
            # A bit faster than return(''.join(out[::-1])); avoids creating new
            # list.
            out.reverse()
            return ''.join(out)
        else:
            raise ValueError('"{}" must be positive integer to convert it to '
                    'given base.'.format(int_id))

    def base_to_int(self, base_id):
        """Translate a base representation to an integer."""
        if self.is_valid_base_id_form(base_id):
            base_id = base_id.strip()
            r = lambda i: self.base.index(base_id[len(base_id)-i-1]) * \
                    len(self.base)**i
            return sum([r(j) for j in range(len(base_id))])
        else:
            raise ValueError('"{}" is not a valid ID in the given base.'
                    .format(base_id))

    def is_valid_base_id_form(self, base_id):
        """Return true/false if string is a valid representation in the given
        base. Raises TypeError if input is not a string."""
        try:
            return not base_id.strip().translate(None, self.base)
        except AttributeError:
            raise TypeError('representation must be a string.')

    def is_valid_int_id_form(self, int_id):
        """Return true/false if input is/can be converted to a valid integer
        representation of a mapping in the given base. Raises TypeError if
        input is not of integer form."""
        try:
            return int(int_id) > 0 and int_id == int(int_id)
        except ValueError:
            return TypeError('{} should be an integer.'.format(int_id))


class BaseItem(Translation):
    """An item defined by its ID mapping in the given base."""
    def __init__(self, base, base_id):
        self.base = base
        if self.is_valid_base_id_form(base_id):
            # Whitespace at either end is ignored anyway.
            self._base_id = base_id.strip()
        else:
            raise ValueError('short representation "{}" not valid in given '
                    'base.'.format(base_id))

        int_id = self.base_to_int(base_id)

        if self.is_valid_int_id_form(int_id):
            self._int_id = int_id
        else:
            raise ValueError('internal error: {} is not a valid integer ID.'
                    .format(int_id))

    @property
    def base_id(self):
        return self._base_id

    @property
    def int_id(self):
        return self._int_id


class TestSequence(unittest.TestCase):
    def setUp(self):
        self.representation = '''
            abcdefghijk mnopqrstuvwxyz
            A CDEFGH JKLMN PQR TUVWXYZ
              234 67 9
          	'''
        # Precalculated values.
        self.base_id = 'An'
        self.int_id = 1337

        self.translation = Translation(self.representation)
        self.base_item = BaseItem(self.representation, self.base_id)

    def test_translation_init(self):
        """Check intialization of invalid bases in Translation."""
        with self.assertRaises(ValueError):
            Translation('aaa')
        with self.assertRaises(TypeError):
            Translation(123)
        with self.assertRaises(TypeError):
            Translation(('a', 'b', 'c'))
        with self.assertRaises(ValueError):
            Translation(' ')
        with self.assertRaises(ValueError):
            Translation('\t')
        with self.assertRaises(ValueError):
            Translation('\n')

    def test_translation_functions(self):
        """Check function calls with invalid arguments and that item
        translation is bidirectionally consistent in Translation."""
        with self.assertRaises(TypeError):
            self.translation.int_to_base('Five')
        with self.assertRaises(ValueError):
            self.translation.int_to_base(-1)
        with self.assertRaises(ValueError):
            self.translation.int_to_base(2.7)
        with self.assertRaises(ValueError):
            self.translation.base_to_int('lBIOS1580')

        self.assertEqual(
                self.translation.int_to_base(self.int_id), self.base_id)
        self.assertEqual(
                self.translation.base_to_int(self.base_id), self.int_id)

        # Check that whitespace is correctly stripped.
        self.assertEqual(
                self.translation.base_to_int(' \t\n' + self.base_id + ' \t\n'),
                self.int_id)

    def test_base_item_init(self):
        """Test initialization with invalid arguments and that whitespace is
        handled correctly in BaseItem."""
        with self.assertRaises(TypeError):
            BaseItem(self.representation, self.int_id)
        with self.assertRaises(ValueError):
            BaseItem(self.representation, 'lBIOS1580')
        with self.assertRaises(AttributeError):
            self.base_item.base_id = 'cat'
        with self.assertRaises(AttributeError):
            self.base_item.int_id = self.int_id + 1

        # Check that whitespace is correctly stripped.
        with_space = BaseItem(self.representation,
                              ' \t\n' + self.base_id + ' \t\n')
        self.assertEqual(with_space.int_id, self.base_item.int_id)

    def test_base_item_calc(self):
        """Check concistency in bidirectional translation in BaseItem."""
        self.assertEqual(self.base_item.base_id, self.base_id)
        self.assertEqual(self.base_item.int_id, self.int_id)

        # Check that whitespace is correctly stripped.
        with_space = BaseItem(self.representation,
                              ' \t\n' + self.base_id + ' \t\n')
        self.assertEqual(with_space.base_id, self.base_id)
        self.assertEqual(with_space.int_id, self.int_id)


def main():
    unittest.main()


if __name__ == '__main__':
    main()

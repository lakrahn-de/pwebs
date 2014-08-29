# Copyright (C) 2014-2014 Project
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher

import unittest
from pwebs import main


class TestMain(unittest.TestCase):
    def test_threshold(self):
        import argparse
        self.assertSequenceEqual(main.threshold('i25,o30,i20,o40'),
                                 ((0, 25), (0, 30)))
        with self.assertRaises(argparse.ArgumentTypeError):
            main.threshold('iab,ocd')
        self.assertSequenceEqual(main.threshold('i25:30,o30:35'),
                                 ((25, 30), (30, 35)))
        with self.assertRaises(argparse.ArgumentTypeError):
            main.threshold('i24:20,o30:40')
        with self.assertRaises(argparse.ArgumentTypeError):
            main.threshold('i24:30,o30:25')
        self.assertSequenceEqual(main.threshold('i~:30,o30:35'),
                                 (('~', 30), (30, 35)))
        self.assertSequenceEqual(main.threshold('i20:30,o~:35'),
                                 ((20, 30), ('~', 35)))
        self.assertSequenceEqual(main.threshold('in~:30,out~:35'),
                                 (('~', 30), ('~', 35)))
        self.assertSequenceEqual(main.threshold('i22'), ((0, 22), None))

    def test_is_in_range(self):
        self.assertTrue(main._is_in_range(20, '~', 20))
        self.assertTrue(main._is_in_range(20, 15, 20))
        self.assertTrue(main._is_in_range(0, '~', 10))
        self.assertFalse(main._is_in_range(0, 10, 20))

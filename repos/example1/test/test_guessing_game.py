import unittest
import sys, os.path
sys.path.append(os.path.abspath('../'))
from example1.src import guessing_game as example

class TestExample(unittest.TestCase):
    def test_get_number(self):
        self.assertGreaterEqual(example.get_number(), 1)
        self.assertLessEqual(example.get_number(), 10)

    def test_guess_true(self):
        self.assertEqual(example.guess(3, 3), True)

    def test_guess_false(self):
        self.assertEqual(example.guess(4, 6), False)

    def test_foo_true(self):
        self.assertEqual(example.foo(4), True)

    def test_foo_true_negative(self):
        self.assertEqual(example.foo(-2), True)

    def test_foo_false(self):
        self.assertEqual(example.foo(9), False)

    def test_crypto_func(self):
        self.assertGreaterEqual(example.crypto_func(), -10)
        self.assertLessEqual(example.crypto_func(), 10)

if __name__ == '__main__':
    unittest.main()


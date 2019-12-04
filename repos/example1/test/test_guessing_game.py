import unittest
import sys, os.path
sys.path.append(os.path.abspath('../'))
from example1.src import guessing_game as example

class TestExample(unittest.TestCase):
    def test_get_number(self):
        self.assertGreaterEqual(example.get_number(), 1)
        self.assertLessEqual(example.get_number(), 10)

    def test_guess(self):
        self.assertEqual(example.guess(4, 6), False)
        self.assertEqual(example.guess(3, 3), True)

    def test_true(self):
        self.assertTrue(True)

    def test_false_one(self):
        self.assertTrue(False)

    def test_false_two(self):
        self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()


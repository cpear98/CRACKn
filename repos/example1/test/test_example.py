import unittest
from src import example

class TestExample(unittest.TestCase):
    def test_get_number(self):
        self.assertGreaterEqual(example.get_number(), 1)
        self.assertLessEqual(example.get_number(), 10)

    def test_guess(self):
        self.assertEqual(example.guess(4, 6), False)
        self.assertEqual(example.guess(3, 3), True)

if __name__ == '__main__':
    unittest.main()


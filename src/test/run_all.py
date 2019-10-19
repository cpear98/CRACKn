import unittest
from test.test_arg_parser import TestArgParser

if __name__ == '__main__':
    test_list = []
    test_list.append(unittest.TestLoader().loadTestsFromTestCase(TestArgParser))
    suite = unittest.TestSuite(test_list)
    unittest.TextTestRunner(buffer=True).run(suite)
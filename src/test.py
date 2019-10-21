import unittest
from test.test_cli_parser import TestCLIParser

if __name__ == '__main__':
    test_list = []
    test_list.append(unittest.TestLoader().loadTestsFromTestCase(TestCLIParser))
    suite = unittest.TestSuite(test_list)
    unittest.TextTestRunner(buffer=True).run(suite)
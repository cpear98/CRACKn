import unittest
from crackn.parsing.cli_parser import CLIParser, Languages, Frameworks

class TestCLIParser(unittest.TestCase):
    # Test CLIParser.parse_cli method
    def test_parse_cli_exits_with_no_args(self):
        args = []
        parser = CLIParser(args, check_assertions=True)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_bad_param(self):
        args = ['bad_param=bad_val']
        parser = CLIParser(args, check_assertions=True)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_bad_param_value(self):
        args = ['good_param=bad_val']
        parser = CLIParser(args, check_assertions=True)
        parser.add_param('good_param', {'good_val'}) # add good_param to the parser as a valid command line flag with "good_val" as a valid value
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_long_flag(self):
        args = ['-long']
        parser = CLIParser(args, check_assertions=True)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_non_existant_flag(self):
        args = ['-w']
        parser = CLIParser(args, check_assertions=True)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_random_args(self):
        args = ['random1', 'random2', 'random3']
        parser = CLIParser(args, check_assertions=True)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_good_param_bad_flag(self):
        args = ['good_param=good_value', '-w']
        parser = CLIParser(args, check_assertions=True)
        parser.add_param('good_param', {'good_val'}) # add good_param to the parser as a valid command line flag with "good_val" as a valid value
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_good_flag_bad_param(self):
        args = ['-g', 'bad_param=bad_val']
        parser = CLIParser(args, check_assertions=True)
        parser.add_flag('-g', None) # add g to the parser as a valid command line flag
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_good_params(self):
        args = ['sdir=.', 'tdir=test', 'good_param=good_val2']
        parser = CLIParser(args, check_assertions=True)
        parser.add_param('good_param', {'good_val1', 'good_val2'})
        parser.parse_cli()
        oracle = {'sdir': '.', 'tdir': 'test', 'lang': Languages.PYTHON, 'framework': Frameworks.UNITTEST, 'good_param': 'good_val2'}
        for key in oracle:
            self.assertEqual(parser.get_parameter(key).get_value(), oracle[key])

    def test_parse_cli_one_good_flag(self):
        args = ['sdir=.', 'tdir=test', '-g']
        parser = CLIParser(args, check_assertions=True)
        parser.add_flag('-g', None)
        parser.parse_cli()
        param_oracle = {'sdir': '.', 'tdir': 'test', 'lang': Languages.PYTHON, 'framework': Frameworks.UNITTEST}
        flag_oracle = {'-h': False, '-g': True, '-s': False, '-t': False}
        for key in param_oracle:
            self.assertEqual(parser.get_parameter(key).get_value(), param_oracle[key])
        for key in flag_oracle:
            self.assertEqual(parser.get_flag(key).get_value(), flag_oracle[key])

    def test_parse_cli_multiple_good_params(self):
        args = ['sdir=.', 'tdir=test', 'good_param1=val1', 'good_param2=val3']
        parser = CLIParser(args, check_assertions=True)
        parser.add_param('good_param1', {'val1', 'val2'})
        parser.add_param('good_param2', {'val3', 'val4'})
        parser.parse_cli()
        param_oracle = {'sdir': '.', 'tdir': 'test', 'lang': Languages.PYTHON, 'good_param1': 'val1', 'good_param2': 'val3'}
        for key in param_oracle:
            self.assertEqual(parser.get_parameter(key).get_value(), param_oracle[key])

    def test_parse_cli_multiple_good_flags(self):
        args = ['sdir=.', 'tdir=test', '-g', '-u', '-v'] # currently -g, -t, -v have no real functionality. if these flags are added as actual functional flags, this test should be updated
        parser = CLIParser(args, check_assertions=True)
        parser.add_flag('-g', None)
        parser.add_flag('-u', None)
        parser.add_flag('-v', None)
        parser.parse_cli()
        flag_oracle = {'-g': True, '-g': True, '-u': True, '-v': True, '-h': False}
        for key in flag_oracle:
            self.assertEqual(parser.get_flag(key).get_value(), flag_oracle[key])

    # Test CLIParser.parse_param method
    def test_parse_param(self):
        pass

    # Test CLIParser.parse_flag method
    def test_parse_flag(self):
        pass

    # Test CLIParser.has_basic_requirements method
    def test_has_basic_requirements(self):
        pass

    # Test CLIParser.is_valid_flag method
    def test_is_valid_flag(self):
        pass

    # Test CLIParser.is_valid_param method
    def test_is_valid_param(self):
        pass

if __name__ == '__main__':
    unittest.main(buffer=True)
import unittest
from crackn.arg_parser import ArgParser, InvalidArgumentException

class TestArgParser(unittest.TestCase):
    def test_parse_cli_exits_with_no_args(self):
        args = []
        parser = ArgParser(args)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_bad_param(self):
        args = ['bad_param=bad_val']
        parser = ArgParser(args)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_bad_param_value(self):
        args = ['good_param=bad_val']
        parser = ArgParser(args)
        parser.param_values['good_param'] = {'good_val'} # add good_param to the parser as a valid command line flag with "good_val" as a valid value
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_long_flag(self):
        args = ['-long']
        parser = ArgParser(args)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_non_existant_flag(self):
        args = ['-w']
        parser = ArgParser(args)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_random_args(self):
        args = ['random1', 'random2', 'random3']
        parser = ArgParser(args)
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_good_param_bad_flag(self):
        args = ['good_param=good_value', '-w']
        parser = ArgParser(args)
        parser.param_values['good_param'] = {'good_val'} # add good_param to the parser as a valid command line flag with "good_val" as a valid value
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_cli_exits_with_good_flag_bad_param(self):
        args = ['-g', 'bad_param=bad_val']
        parser = ArgParser(args)
        parser.flags['g'] = False # add g to the parser as a valid command line flag
        with self.assertRaises(SystemExit) as sys_exit:
            parser.parse_cli()
        self.assertEqual(sys_exit.exception.code, 1)

    def test_parse_param(self):
        pass

    def test_parse_flag(self):
        pass

    def test_has_basic_requirements(self):
        pass

    def test_is_valid_flag(self):
        pass

    def test_is_valid_param(self):
        pass

if __name__ == '__main__':
    unittest.main()
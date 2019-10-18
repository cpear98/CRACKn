import sys

class ArgParser():
    def __init__(self):
        self.arg_descriptions = {'dir': 'The directory containing the Python source code you would like to analyze.'}
        self.arg_values = {'dir': None}

    def parse_cli(self):
        for arg in sys.argv[1:]:
            arg_id, arg_val = arg.split('=')
            if arg_id not in self.arg_values:
                ArgParser.print_unrecognized_arg(arg_id)
                self.print_usage()
                exit(1)
            self.arg_values[arg_id] = arg_val
    
    def print_usage(self):
        print('Temp usage message')

    @staticmethod
    def print_unrecognized_arg(arg):
        print(f'Unrecognized argument: {arg}')
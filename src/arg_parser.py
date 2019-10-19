class InvalidArgumentException(Exception):
    pass

class ArgParser():
    def __init__(self, args):
        self.args = args
        self.param_descriptions = {'dir': 'The directory containing the Python source code you would like to analyze.'}
        self.params = {'dir': None}
        self.flag_descriptions = {'h': 'Display this help message'}
        self.flags = {'h': False}

    def parse_cli(self):
        try:
            for arg in self.args:
                if arg[0] == '-':
                    self.parse_flag(arg[1:])
                else:
                    self.parse_param(arg)
        except InvalidArgumentException as e:
            self.print_unrecognized_arg(e)
            self.print_usage()
            exit(1)
        if not self.has_basic_requirements():
            self.print_usage()
            exit(1)

    def parse_param(self, param):
        split_param = param.split('=')
        if not self.is_valid_param(split_param):
            raise InvalidArgumentException(param)
        self.params[split_param[0]] = split_param[1]

    def parse_flag(self, flag):
        if not self.is_valid_flag(flag):
            raise InvalidArgumentException(f'-{flag}')
        self.flags[flag] = True

    def has_basic_requirements(self):
        # TODO: stub
        if self.params['dir'] is not None:
            return True
        return False
    
    def print_usage(self):
        print('Temp usage message')

    def is_valid_flag(self, flag):
        return len(flag) == 1 and flag in self.flags

    def is_valid_param(self, param):
        return len(param) == 2 and param[0] != '' and param[1] != '' and param[0] in self.params

    @staticmethod
    def print_unrecognized_arg(arg):
        print(f'Unrecognized argument: {arg}')
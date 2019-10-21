class InvalidArgumentException(Exception):
    pass

class CLIParser():
    def __init__(self, args, check_assertions=False):
        self.args = args
        self.param_descriptions = {'dir': 'The directory containing the Python source code you would like to analyze.',
                                   'language': 'The language the source code to be analyzed is written in.'}
        self.param_values = {'dir': None,
                             'language': {'Python'}} # dictionary mapping parameters to a set of values they can take. if any value is allowed, the param has a value of None
        self.params = {'dir': None, 'language': 'Python'}
        self.flag_descriptions = {'h': 'Display this help message'}
        self.flags = {'h': False}
        self.check_assertions = check_assertions
        if check_assertions:
            self.check_shape()

    def check_shape(self): # checks runs assertions to ensure class invariants are held
        assert(self.param_descriptions.keys() == self.param_values.keys() == self.params.keys())
        assert(self.flag_descriptions.keys() == self.flags.keys())

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
        if self.check_assertions:
            self.check_shape()

    def parse_param(self, param):
        split_param = param.split('=')
        if not self.is_valid_param(split_param):
            raise InvalidArgumentException(param)
        self.params[split_param[0]] = split_param[1]
        if self.check_assertions:
            self.check_shape()

    def parse_flag(self, flag):
        if not self.is_valid_flag(flag):
            raise InvalidArgumentException(f'-{flag}')
        self.flags[flag] = True
        if self.check_assertions:
            self.check_shape()

    def has_basic_requirements(self):
        if self.params['dir'] is not None:
            return True
        return False
    
    def print_usage(self):
        print('Temp usage message')

    def is_valid_flag(self, flag):
        return len(flag) == 1 and flag in self.flags

    def is_valid_param(self, param):
        return len(param) == 2 and param[0] != '' and param[1] != '' and param[0] in self.params and (self.param_values[param[0]] is None or param[1] in self.param_values[param[0]])

    def add_param(self, param, values, default=None, desc=''):
        # TODO: add param sanitation before adding
        if param in self.params:
            print(f'Parameter {param} already exists.')
            return False
        self.params[param] = default
        self.param_values[param] = values
        self.param_descriptions[param] = desc
        if self.check_assertions:
            self.check_shape()
        return True

    def add_flag(self, flag, desc=''):
        # TODO: more flag sanitation
        if flag in self.flags:
            print(f'Flag {flag} already exists.')
            return False
        self.flags[flag] = False
        self.flag_descriptions[flag] = desc
        if self.check_assertions:
            self.check_shape()
        return True

    @staticmethod
    def print_unrecognized_arg(arg):
        print(f'Unrecognized argument: {arg}')
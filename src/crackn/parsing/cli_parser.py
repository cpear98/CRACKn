from enum import Enum

# The languages supported by CRACKn
class Languages(Enum):
    PYTHON = 0

class Frameworks(Enum):
    UNITTEST = 0

class InvalidArgumentException(Exception):
    pass

class NonExistantParameterException(Exception):
    pass

class NonExistantFlagException(Exception):
    pass

class Parameter():
    def __init__(self, name, description, available_values, default_value, required=False, check_assertions=False):
        self.name = name
        self.description = description
        self.available_values = available_values
        self._value = default_value
        self.required = required
        self.check_assertions = check_assertions
        if self.check_assertions:
            self.check_shape()

    def is_valid_value(self, value):
        return self.available_values is None or value in self.available_values

    def set_value(self, value):
        if self.is_valid_value(value):
            self._value = value
            return True
        else:
            print(f'[ERROR]: Attempted to set parameter {self.name} to value {value} which is not an available value.')
            return False
        if self.check_assertions:
            self.check_shape()

    def get_value(self):
        return self._value

    def check_shape(self):
        # TODO: stub
        return True

class Flag():
    def __init__(self, short_id, long_id, description, check_assertions=False):
        self.short = short_id
        self.long = long_id
        self.description = description
        self._value = False
        self.check_assertions = check_assertions
        if self.check_assertions:
            self.check_shape()

    def set_flag(self):
        self._value = True

    def get_value(self):
        return self._value

    def set_check_assertions(self, value):
        self.check_assertions = value

    def check_shape(self):
        # the flag needs at least one id
        if self.short is None: assert(self.long is not None)
        if self.long is None: assert(self.short is not None)

        # check that ids have the correct format
        if self.short is not None: assert(len(self.short) == 2 and self.short[0] == '-')
        if self.long is not None: assert(self.long[:2] == '--')

# instantiate parameters as objects
param_source_dir = Parameter('sdir', 'The directory containing the Python source code you would like to analyze.', None, None, required=True)
param_test_dir = Parameter('tdir', 'The directory containing the unit tests for the source code in src-dir', None, None, required=True)
param_language = Parameter('lang', 'The language the source code to be analyzed is written in.', {Languages.PYTHON}, Languages.PYTHON)
param_test_framework = Parameter('framework', 'The test framework the supplied unit tests are written with.', {Frameworks.UNITTEST}, Frameworks.UNITTEST)
parameters = {param_source_dir, param_test_dir, param_language, param_test_framework}

# instantiate flags as objects
flag_help = Flag('-h', '--help', 'Display this help message.')
flag_test = Flag('-t', '--test', 'Run the unit tests for CRACKn.')
flag_silent = Flag('-s', '--silent', 'Run CRACKn in silent mode (no extraneous command line output).')
flags = {flag_help, flag_test, flag_silent}

class CLIParser():
    def __init__(self, args, check_assertions=False):
        self.args = args

        # map parameter names to their data structure for constant time access
        self.parameters = dict()
        for parameter in parameters:
            self.parameters[parameter.name] = parameter

        # map flag names to their data structure for constant time access
        self.flags = dict()
        for flag in flags:
            # check if short and long ids exist and if they do map both to their data structure so it can be access via either name
            if flag.short is not None:
                self.flags[flag.short] = flag
            if flag.long is not None:
                self.flags[flag.long] = flag

        # check_assertions should be false in a production environment
        self.check_assertions = check_assertions
        if check_assertions:
            self.check_shape()

    def check_shape(self): # checks runs assertions to ensure class invariants are held
        # TODO: stub
        pass

    # parse the arguments given on the command line for parameters and flags
    def parse_cli(self):
        try:
            for arg in self.args:
                if arg[0] == '-':
                    self.parse_flag(arg)
                else:
                    self.parse_param(arg)
        except NonExistantParameterException as e:
            # TODO: handle better
            print(e)
            exit(1)
        except NonExistantFlagException as e:
            # TODO: handle better
            print(e)
            exit(1)
        except InvalidArgumentException as e:
            # TODO: double check handling
            self.print_unrecognized_arg(e)
            self.print_usage()
            exit(1)

        # after parsing all arguments, check to see if the required parameters are set
        if not self.has_basic_requirements():
            self.print_usage()
            exit(1)

        if self.check_assertions:
            self.check_shape()

    def parse_param(self, param):
        split_param = param.split('=')
        if not self.is_valid_param(split_param):
            raise InvalidArgumentException(param)

        # if the argument has the correct format and is a valid parameter set the value of param[0] to be param[1]
        # can raise NonExistantParameterException
        self.get_parameter(split_param[0]).set_value(split_param[1])
        if self.check_assertions:
            self.check_shape()

    def parse_flag(self, flag):
        if not self.is_valid_flag(flag):
            raise InvalidArgumentException(flag)
        
        # if the arg has the correct format and is a valid flag set the value of the flag to true
        self.get_flag(flag).set_flag()
        if self.check_assertions:
            self.check_shape()

    def has_basic_requirements(self):
        for parameter in self.parameters:
            param_obj = self.parameters[parameter]
            if param_obj.required and param_obj.get_value() is None:
                return False
        return True
    
    def print_usage(self):
        print('Usage: crackn src=')

    def print_help(self):
        self.print_usage()

    def is_valid_flag(self, flag):
        return flag in self.flags

    def is_valid_param(self, param):
        # param is a list with form [name, val] where the original input was name=val
        return len(param) == 2 and param[0] != '' and param[1] != '' and param[0] in self.parameters and self.parameters[param[0]].is_valid_value(param[1])

    def add_param(self, param, values, default=None, desc=''):
        # TODO: add param sanitation before adding
        if param in self.parameters:
            print(f'Parameter {param} already exists.')
            return False
        self.parameters[param] = Parameter(param, desc, values, default)
        if self.check_assertions:
            self.check_shape()
        return True

    def add_flag(self, short_id, long_id, desc=''):
        # TODO: more flag sanitation
        if short_id in self.flags or long_id in self.flags:
            print(f'Flag ({short_id}, {long_id}) already exists.')
            return False
        new_flag = Flag(short_id, long_id, desc)
        if new_flag.short is not None:
            self.flags[short_id] = new_flag
        if new_flag.long is not None:
            self.flags[long_id] = new_flag
        if self.check_assertions:
            self.check_shape()
        return True

    def get_parameter(self, param):
        assert(type(param) == str)
        if param in self.parameters:
            return self.parameters[param]
        raise NonExistantParameterException(param)

    def get_flag(self, flag):
        assert(type(flag) == str)
        if flag in self.flags:
            return self.flags[flag]
        raise NonExistantFlagException(flag)

    @staticmethod
    def print_unrecognized_arg(arg):
        print(f'Unrecognized argument: {arg}')
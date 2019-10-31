from enum import Enum

# Helper method for getting an enum value from a string
def enum_from_string(enum_dict, string):
    string = string.lower()
    if string in enum_dict:
        return enum_dict[string]
    return None

# The languages supported by CRACKn
class Language(Enum):
    PYTHON = 0

    @classmethod
    def from_string(self, string):
        return enum_from_string({'python': self.PYTHON}, string)

    @classmethod
    def get_string(self, string):
        language_dict = {self.PYTHON: 'Python'}
        return language_dict[string]

# The frameworks supported by CRACKn
class Framework(Enum):
    UNITTEST = 0

    @classmethod
    def from_string(self, string):
        return enum_from_string({'unittest': self.UNITTEST}, string)

    @classmethod
    def get_string(self, string):
        framework_dict = {self.UNITTEST: 'unittest'}
        return framework_dict[string]

class InvalidArgumentException(Exception):
    pass

class NonExistantParameterException(Exception):
    pass

class NonExistantFlagException(Exception):
    pass

class MissingRequiredParameterException(Exception):
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
        return self.available_values is None \
               or value in self.available_values \
               or Language.from_string(value) in self.available_values \
               or Framework.from_string(value) in self.available_values

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
param_language = Parameter('lang', 'The language the source code to be analyzed is written in.', {Language.PYTHON}, Language.PYTHON)
param_test_framework = Parameter('framework', 'The test framework the supplied unit tests are written with.', {Framework.UNITTEST}, Framework.UNITTEST)
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
        self._parameters = dict()
        for parameter in parameters:
            self._parameters[parameter.name] = parameter

        # map flag names to their data structure for constant time access
        self._flags = dict()
        for flag in flags:
            # check if short and long ids exist and if they do map both to their data structure so it can be access via either name
            if flag.short is not None:
                self._flags[flag.short] = flag
            if flag.long is not None:
                self._flags[flag.long] = flag

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
        try:
            self.has_basic_requirements()
        except MissingRequiredParameterException as e:
            print(f'[ERROR]: Missing required parameter: {e}.')
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
        if self.get_flag('-h').get_value():
            return
        for parameter in self.get_parameters():
            if parameter.required and parameter.get_value() is None:
                raise MissingRequiredParameterException(parameter.name)
    
    def print_usage(self):
        print('Usage: crackn sdir=<source directory> tdir=<test directory> [parameters] [flags]')

    def print_help(self):
        self.print_usage()
        print('\nPARAMETERS\n')
        print('Parameters have the form param=value where "param" is the parameter name and "value" is the value to assign to it.\n')

        # print parameters
        for parameter in self.get_parameters():
            entry = f'{parameter.name}   {parameter.description}\nPossible values: '
            values = ''
            if parameter.available_values is None:
                values = 'Any value\n'
            else:
                values = '['
                for value in parameter.available_values:
                    if type(value) == Language:
                        values += Language.get_string(value)
                    elif type(value) == Framework:
                        values += Framework.get_string(value)
                    else:
                        values += value
                    values += ', '
                # remove the ', ' from the end and close the brackets
                values = values[:-2] + ']'
            entry += values
            print(entry)

        print('\nFLAGS\n')
        print('Flags have the form -f or --flag.\n')

        # print flags
        for flag in self.get_flags():
            entry = ''
            if flag.short is not None:
                entry += flag.short
            if flag.long is not None:
                if len(entry) > 0:
                    entry += f' ({flag.long})'
                else:
                    entry += flag.long
            entry += f'   {flag.description}\n'
            print(entry)

    def is_valid_flag(self, flag):
        return flag in self._flags

    def is_valid_param(self, param):
        # param is a list with form [name, val] where the original input was name=val
        return len(param) == 2 and param[0] != '' and param[1] != '' and param[0] in self._parameters and self.get_parameter(param[0]).is_valid_value(param[1])

    def add_param(self, param, values, default=None, desc=''):
        # TODO: add param sanitation before adding
        if param in self._parameters:
            print(f'Parameter {param} already exists.')
            return False
        self._parameters[param] = Parameter(param, desc, values, default)
        if self.check_assertions:
            self.check_shape()
        return True

    def add_flag(self, short_id, long_id, desc=''):
        # TODO: more flag sanitation
        if short_id in self._flags or long_id in self._flags:
            print(f'Flag ({short_id}, {long_id}) already exists.')
            return False
        new_flag = Flag(short_id, long_id, desc)
        if new_flag.short is not None:
            self._flags[short_id] = new_flag
        if new_flag.long is not None:
            self._flags[long_id] = new_flag
        if self.check_assertions:
            self.check_shape()
        return True

    def get_parameter(self, param):
        assert(type(param) == str)
        if param in self._parameters:
            return self._parameters[param]
        raise NonExistantParameterException(param)

    def get_parameters(self):
        return [self._parameters[key] for key in self._parameters.keys()]

    def get_flag(self, flag):
        assert(type(flag) == str)
        if flag in self._flags:
            return self._flags[flag]
        raise NonExistantFlagException(flag)

    def get_flags(self):
        seen = set()
        for key in self._flags:
            flag = self.get_flag(key)
            if flag in seen:
                pass
            seen.add(flag)
        return list(seen)

    @staticmethod
    def print_unrecognized_arg(arg):
        print(f'Unrecognized argument: {arg}')
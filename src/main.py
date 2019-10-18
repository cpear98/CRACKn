import subprocess
from arg_parser import ArgParser

if __name__ == '__main__':
    parser = ArgParser()
    parser.parse_cli()
    directory = parser.arg_values['dir']
    result = subprocess.run(['bandit', '-r', directory])
    print(result)
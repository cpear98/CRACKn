import subprocess
import sys
from arg_parser import ArgParser

if __name__ == '__main__':
    parser = ArgParser(sys.argv[1:])
    parser.parse_cli()

    if parser.flags['h']:
        parser.print_usage()
        exit(0)

    directory = parser.params['dir']
    result = subprocess.run(['bandit', '-r', directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
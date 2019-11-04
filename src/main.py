import subprocess
import sys
from crackn.parsing.cli_parser import CLIParser

if __name__ == '__main__':
    parser = CLIParser(sys.argv[1:])
    parser.parse_cli()

    if parser.get_flag('-h').get_value():
        parser.print_help()
        exit(0)

    directory = parser.get_parameter('repo').get_value()
    print('[INFO]: Running Bandit...')
    task_complete = False
    result = None
    while(not task_complete):
        try:
            result = subprocess.run(['bandit', '-r', directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10.0)
            task_complete = True
        except TimeoutError:
            pass
    print(result)
    print('[INFO]: Bandit analysis complete.')
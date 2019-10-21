import subprocess
import sys
from crackn.parsing.cli_parser import CLIParser

if __name__ == '__main__':
    parser = CLIParser(sys.argv[1:])
    print('Initialized Parser.')
    parser.parse_cli()
    print('Parsed CLI arguments.')

    if parser.flags['h']:
        parser.print_usage()
        exit(0)

    directory = parser.params['dir']
    print('Running Bandit...')
    task_complete = False
    while(not task_complete):
        try:
            result = subprocess.run(['bandit', '-r', directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10.0)
            task_complete = True
        except TimeoutError:
            pass
    print('Bandit analysis complete.')
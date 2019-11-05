import subprocess
import sys
import os
from crackn.parsing.cli_parser import CLIParser
from crackn.parsing.bandit_parser import BanditReport

if __name__ == '__main__':
    cli_parser = CLIParser(sys.argv[1:])
    cli_parser.parse_cli()

    if cli_parser.get_flag('-h').get_value():
        cli_parser.print_help()
        exit(0)

    # check if the user requested to run in silent/suppressed mode
    silent_mode = cli_parser.get_flag('-s').get_value()
    # print a warning that Bandit output may look different when printed
    if not silent_mode:
        print('[INFO]: Running with silent mode turned OFF. Please note this may cause some output to lose formatting and/or coloring.\n')

    repo_name = cli_parser.get_parameter('repo').get_value()
    repo_path = os.path.abspath(__file__ + f'/../../repos/{repo_name}')
    if not os.path.exists(repo_path):
        print(f'[ERROR]: Repo "{repo_name}" not found. Please create the appropriate directories in CRACKn/repos.')
        exit(1)
    if not os.path.exists(repo_path + '/src') or not os.path.exists(repo_path + '/test'):
        print(f'[ERROR]: Repo "{repo_name}" found but is missing required subdirectories. Please ensure "{repo_name}/src" and "{repo_name}/test" exist.')
        exit(1)
    
    print('[INFO]: Running Bandit...')
    task_complete = False
    result = None
    while(not task_complete):
        try:
            result = subprocess.run(['bandit', '-r', repo_path + '/src'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10.0)
            task_complete = True
        except TimeoutError:
            pass
    print('[INFO]: Bandit analysis complete.')

    bandit_output = result.stdout.decode('utf-8')
    if not silent_mode:
        print(bandit_output)

    print('[INFO]: Parsing Bandit report...')
    bandit_report = BanditReport(bandit_output, auto_parse=True)

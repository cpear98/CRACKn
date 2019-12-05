import subprocess
import sys
import os
from crackn.parsing.cli_parser import CLIParser
from crackn.parsing.bandit_parser import BanditReport
from crackn.genetics.mutations import GeneticSimulator, Population, Chromosome
import crackn.settings as settings
import crackn.logging as Log

if __name__ == '__main__':
    cli_parser = CLIParser(sys.argv[1:])
    cli_parser.parse_cli()

    if cli_parser.get_flag('-h').get_value():
        cli_parser.print_help()
        exit(0)

    # check if the user requested to run in silent/suppressed mode
    silent_mode = cli_parser.get_flag('-s').get_value()

    # initialize the settings module and set the silent mode
    settings.init()
    settings.set_silent(silent_mode)

    # print a warning that Bandit output may look different when printed
    if not silent_mode:
        Log.INFO('Running with silent mode turned OFF. Please note this may cause some output to lose formatting and/or coloring.\n')

    repo_name = cli_parser.get_parameter('repo').get_value()
    repo_path = os.path.abspath(__file__ + f'/../../repos/{repo_name}')
    if not os.path.exists(repo_path):
        Log.ERROR(f'Repo "{repo_name}" not found. Please create the appropriate directories in CRACKn/repos.')
        exit(1)
    if not os.path.exists(repo_path + '/src') or not os.path.exists(repo_path + '/test'):
        Log.ERROR(f'Repo "{repo_name}" found but is missing required subdirectories. Please ensure "{repo_name}/src" and "{repo_name}/test" exist.')
        exit(1)
    
    simulators = []
    source_files = set()
    source_files_with_tests = set()

    Log.INFO('Scanning for source files...')
    for entry in os.scandir(f'{repo_path}/src'):
        if entry.name[-3:] == '.py' and entry.name[0] != '_':
            source_files.add(entry.name)
    Log.INFO('Found files:')
    for file_name in source_files:
        Log.INFO(f'    - {file_name}')
    print()

    Log.INFO('Scanning for unit test files...')
    for entry in os.scandir(f'{repo_path}/test'):
        if entry.name[:5] == 'test_' and entry.name[5:] in source_files:
            source_files_with_tests.add(entry.name[5:])
    Log.INFO(f'Found unit tests for files:')
    for file_name in source_files_with_tests:
        simulators.append(GeneticSimulator(file_name, f'test_{file_name}', repo_name))
        Log.INFO(f'    - {file_name}')

    for simulator in simulators:
        simulator.generate_starting_population()
        for chromosome in simulator.population.chromosomes:
            print(chromosome)


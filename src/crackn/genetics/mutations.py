import ast
import astor
import subprocess
import os
from crackn.parsing import bandit_parser, unittest_parser

# a class representing a single potential solution
class Chromosome():
    def __init__(self, population, source=None, source_tree=None):
        if source is None and source_tree is None:
            raise Exception('Attempted to initialize a chromosome without source code or a source code AST.')
        self.source = source
        self.source_tree = source_tree

        if self.source is not None:
            assert(type(source == str), 'Attribute "source" of chromosome must be of type "str".')
            if self.source_tree is None:
                self.source_tree = self.generate_tree()
        else:
            self.source = self.generate_source()

        self.population = population
        self.bandit_report = bandit_parser.BanditReport(source=source, auto_analyze=True, auto_parse=True)
        self.test_results = self.run_tests(population.simulation.test_file, population.simulation.repo)
        self.fitness = self._determine_fitness()

    def __eq__(self, other):
        # TODO: stub
        return False

    def __ne__(self, other):
        # TODO: stub
        return False

    def _determine_fitness(self):
        # TODO: stub
        return float('inf')

    def generate_tree(self, source=None):
        # TODO: stub
        if source is None:
            source = self.source
        return ast.parse(source)

    def generate_source(self, tree=None):
        # TODO: stub
        if tree is None:
            tree = self.source_tree
        return astor.to_source(tree)

    def run_tests(self, test_file, repo):
        current_path = os.path.abspath(os.getcwd())
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{repo}')
        result = subprocess.run(['cd', file_path, '&&', 'python3', f'test/{test_file}', '&&', 'cd', current_path], \
                                stdout=subprocess.PIPE, \
                                stderr=subprocess.STDOUT)
        
        return unittest_parser.UnittestParser.parse(result.stdout.decode('utf-8'))


# a static class containing helper methods for mutating chromosomes
class Mutator():
    @staticmethod
    def crossover(self, chromosome1, chromosome2):
        assert (type(chromosome1) == Chromosome and type(chromosome2) == Chromosome)
        # TODO: stub
        return chromosome1

    @staticmethod
    def mutate(self, chromosome):
        assert (type(chromosome) == Chromosome)
        # TODO: stub
        return chromosome

# a class representing a collection of chromosomes
class Population():
    def __init__(self, simulation):
        # TODO: stub
        self.simulation = simulation
        self.chromosomes = set()

# base class that run a genetic algorithm on a single source code file with an associated unit test file
class GeneticSimulator():
    def __init__(self, source_file, test_file, repo):
        self.source_file = source_file
        self.test_file = test_file
        self.repo = repo
        self.population = Population(self)
        # TODO: stub

    
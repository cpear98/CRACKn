import ast
import astor
import subprocess
import os
import random
from crackn.parsing import bandit_parser as bp, unittest_parser

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
        self.bandit_report = bp.BanditReport(source=source, auto_analyze=True, auto_parse=True)
        self.test_results = self.run_tests(population.simulation.test_file, population.simulation.repo)
        self.fitness = float('inf')
        self._compute_fitness()

    def __eq__(self, other):
        return type(other) == type(self) and self.source == other.source and self.fitness == other.fitness

    def __ne__(self, other):
        return not self.__eq__(other)

    def _compute_fitness(self):
        if self.test_results.crashed or self.test_results.nran == 0:
            self.fitness = float('inf')
        else:
            bandit_fitness_contribution = None
            test_fitness_contribution = None

            if len(self.bandit_report.issues) == 0:
                bandit_fitness_contribution = 0
            else:
                max_issue_rating = 0
                actual_issue_rating = 0

                for issue in self.bandit_report.issues:
                    max_issue_rating += bp.Rating.get_weight(bp.Rating.HIGH) * bp.Rating.get_weight(bp.Rating.HIGH)
                    actual_issue_rating += bp.Rating.get_weight(issue.confidence) * bp.Rating.get_weight(issue.severity)
                bandit_fitness_contribution = float(actual_issue_rating) / max_issue_rating

            test_fitness_contribution = float(self.test_results.nfailing) / self.test_results.nran
            self.fitness = bandit_fitness_contribution + test_fitness_contribution

    def normalize_fitness(self, fitness_sum):
        self.fitness = float(self.fitness) / fitness_sum

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
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{repo}')
        current_path = os.path.abspath(os.getcwd())
        os.chdir(file_path)
        result = subprocess.run(['python3', f'test/{test_file}'], \
                               stdout=subprocess.PIPE, \
                               stderr=subprocess.STDOUT)
        os.chdir(current_path)
        return unittest_parser.UnittestParser.parse(result.stdout.decode('utf-8'))

    def __repr__(self):
        return f'Chromosome: source={self.population.simulation.source_file}, fitness={self.fitness}'

# a static class containing helper methods for mutating chromosomes
class Mutator(ast.NodeTransformer):
    def __init__(self):
        super().__init__(self)
        self._mutate = False
        self._names = set()
        self._num_mutations = 0

    def visit_Name(self, node):
        if self._mutate:
            rand = random.randint(1, 100)
            # only mutate 1% of the time
            if rand == 1:
                self._num_mutations += 1
                print('Need to implement mutation for Name node')
            return node
        else:
            self._names.add(node.id)
            return node

    @staticmethod
    def crossover(self, chromosome1, chromosome2):
        assert (type(chromosome1) == Chromosome and type(chromosome2) == Chromosome)
        # TODO: stub
        return chromosome1

    def mutate(self, source, require_mutation=False):
        assert (type(source) == str)
        tree = ast.parse(source)
        # visit the tree once without mutating to gather information used to make mutations
        self.visit(tree)

        # set the _mutate flag to true to enable mutation when parsing the tree
        self._mutate = True

        # visit the tree again, this time making mutations
        while(True):
            self.visit(tree)
            if not (require_mutation and self._num_mutations < 1):
                break

        # reset the mutators flags and namespace so it can be used again
        self._reset()
        return astor.to_source(tree)

    def _reset(self):
        self._mutate = False
        self._names = set()
        self._num_mutations = 0

# a class representing a collection of chromosomes
class Population():
    def __init__(self, simulation):
        # TODO: stub
        self.simulation = simulation
        self.chromosomes = []

    def add_chromosome(self, source):
        chromosome = Chromosome(self, source=source)
        self.chromosomes.append(chromosome)

# base class that run a genetic algorithm on a single source code file with an associated unit test file
class GeneticSimulator():
    def __init__(self, source_file, test_file, repo, population_size=25, selection_size=10):
        self.source_file = source_file
        self.source = None
        with open(os.path.abspath(__file__ + f'/../../../../repos/{repo}/src/{source_file}')) as f:
            self.source = f.read()
        self.test_file = test_file
        self.repo = repo
        self.population_size = population_size
        self.selection_size = selection_size
        self.population = None

    def generate_starting_population(self):
        # create a new empty population
        population = Population(self)

        # add population_size chromosomes to the population and randomly mutate them, 
        # leaving one unchanged and requiring all other be mutated at least once
        population.add_chromosome(self.source)
        for _ in range(self.population_size - 1):
            pass
            #mutated_source = Mutator.mutate
            #chromosome = Chromosome(population, )
        self.population = population
    
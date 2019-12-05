import ast
import astor
import subprocess
import os
import random
from crackn.parsing import bandit_parser as bp, unittest_parser
import crackn.settings as settings
import crackn.logging as Log

class TestFileModifier(ast.NodeTransformer):
    def __init__(self, filename, uuid):
        super().__init__()
        self.filename = filename
        self.uuid = uuid

    def visit_alias(self, node):
        if node.name == self.filename:
            return ast.alias(name=f'{self.filename}_{self.uuid}', asname=node.asname)
        return node

# a class representing a single potential solution
class Chromosome():
    next_uuid = 0

    def __init__(self, population, source=None, source_tree=None):
        # assign a uuid to this chromosome and then increment the static uuid counter
        self.uuid = Chromosome.next_uuid
        Chromosome.next_uuid += 1

        if source is None and source_tree is None:
            raise Exception('Attempted to initialize a chromosome without source code or a source code AST.')
        self.source = source
        self.source_tree = source_tree

        if self.source is not None:
            Log.INFO('Initialized new chromosome from source')
            assert(type(self.source) == str, 'Attribute "source" of chromosome must be of type "str".')
        else:
            Log.INFO('Initialized new chromosome from AST')
            self.source = self.generate_source()

        self.timeout_occurred = False
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
        if self.timeout_occurred or self.test_results.crashed or self.test_results.nran == 0:
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

    def generate_source(self):
        Log.INFO('Generating source for chromosome from AST')
        assert(self.source_tree is not None)
        return astor.to_source(self.source_tree)

    def modify_test_source(self, original, source_name):
        original_tree = ast.parse(original)
        modifier = TestFileModifier(source_name, self.uuid)
        modifier.visit(original_tree)
        new_source = astor.to_source(original_tree)
        return new_source

    # helper method to create a modified version of the unittest file which uses the source for this chromosome instead of the original source
    def create_test_file(self):
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{self.population.simulation.repo}')
        test_file = self.population.simulation.test_file
        source_file = source_file = self.population.simulation.source_file
        original_test_source = None
        with open(f'{file_path}/test/{test_file}', 'r') as f:
            original_test_source = f.read()
    
        new_test_source = self.modify_test_source(original_test_source, source_file[:-3])

        with open(f'{file_path}/test/{test_file[:-3]}_{self.uuid}.py', 'w') as f:
            f.write(new_test_source)

    def create_source_file(self):
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{self.population.simulation.repo}')
        source_file = self.population.simulation.source_file
        with open(f'{file_path}/src/{source_file[:-3]}_{self.uuid}.py', 'w') as f:
            f.write(self.source)

    def cleanup_files(self):
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{self.population.simulation.repo}')
        test_file = self.population.simulation.test_file
        os.remove(f'{file_path}/test/{test_file[:-3]}_{self.uuid}.py')

        source_file = self.population.simulation.source_file
        os.remove(f'{file_path}/src/{source_file[:-3]}_{self.uuid}.py')

    def test(self, test_file, repo):
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{repo}')
        current_path = os.path.abspath(os.getcwd())
        os.chdir(file_path)

        try:
            result = subprocess.run(['python3', f'test/{test_file}'], \
                                stdout=subprocess.PIPE, \
                                stderr=subprocess.STDOUT, timeout=5)
        except subprocess.TimeoutExpired:
            Log.ERROR(f'TimoutExpired exception occured while attempting to run test file {test_file}')
            self.timeout_occurred = True

        os.chdir(current_path)
        if self.timeout_occurred:
            return None

        return unittest_parser.UnittestParser.parse(result.stdout.decode('utf-8'))

    def run_tests(self, test_file, repo):
        test_file = f'{test_file[:-3]}_{self.uuid}.py'

        # first create the custom unittest file
        self.create_test_file()

        # next create a source file from this chromosome's source code
        self.create_source_file()

        # actually execute the tests with respect to this source
        results = self.test(test_file, repo)

        # cleanup temp files
        self.cleanup_files()

        return results

    def __repr__(self):
        src = self.population.simulation.source_file
        nvuln = len(self.bandit_report.issues)
        nfail = 0 if self.test_results is None else self.test_results.nfailing
        nran = 0 if self.test_results is None else self.test_results.nran
        return f'Chromosome: source={src}, fitness={self.fitness} (nvuln: {nvuln}, nfail: {nfail}/{nran})'

# a static class containing helper methods for mutating chromosomes
class NodeCollector(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.nodes = dict()

    def get_nodes(self):
        return self.nodes

    def visit_any_node(self, node, node_type):
        Log.INFO(f'Visiting node {node} with mutations turned off.')
        if node_type in self.nodes:
            self.nodes[node_type].append(node)
        else:
            self.nodes[node_type] = [node]
        self.generic_visit(node)

    def visit_Name(self, node):
        self.visit_any_node(node, ast.Name)

    def visit_Call(self, node):
        self.visit_any_node(node, ast.Call)

    
class Mutator(ast.NodeTransformer):
    def __init__(self, mutation_frequency=1):
        super().__init__()
        assert(1 <= mutation_frequency <= 100, 'Mutation frequency for Mutator must be between 1 and 100.')
        self.mutation_frequency = mutation_frequency
        self.nodes = None
        self._num_mutations = 0

    def visit_any_node(self, node, node_type):
        Log.INFO(f'Visiting {node_type} node')
        if self.should_mutate():
            Log.INFO(f'Mutating node {node}')
            self._num_mutations += 1
            selected_mutation = self.select_random_mutation()
            Log.INFO(f'Selected mutation: {selected_mutation}')
            return selected_mutation(node)
        else:
            Log.INFO('Returning original node.')
            return node

    def visit_Name(self, node):
        return self.visit_any_node(node, ast.Name)

    def visit_Call(self, node):
        return self.visit_any_node(node, ast.Call)

    def should_mutate(self):
        if random.randint(1, 100) <= self.mutation_frequency:
            Log.INFO(f'Choosing to mutate.')
            return True
        Log.INFO(f'Choosing not to mutate.')
        return False

    # POSSIBLE MUTATION FUNCTIONS
    def delete_node(self, node):
        return None

    def replace_node_with_same_type(self, node):
        # replace the node with another node in the tree of the same type if one exists, else delete the node
        # Note: if the current node is the only node seen of its type this function will always delete it
        if type(node) in self.nodes:
            return random.choice(self.nodes[type(node)])
        return None

    def replace_node_with_any_type(self, node):
        return random.choice(self.nodes[random.choice(list(self.nodes))])

    def replace_node_with_random(self, node):
        Log.INFO(f'Replacing node with call to random number generator.')
        return ast.Call(func=ast.Attribute(value=ast.Name(id='int'), attr='from_bytes'),
                        args=[ast.Call(func=ast.Attribute(value=ast.Name(id='os'), attr='urandom'), args=[ast.Num(n=1)], keywords=[])],
                        keywords=[ast.keyword(arg='byteorder', value=ast.Str(s='big'))])

    # END OF POSSIBLE MUTATION FUNCTIONS

    def select_random_mutation(self):
        return random.choice([self.delete_node,
                              self.replace_node_with_same_type, 
                              self.replace_node_with_any_type, 
                              self.replace_node_with_random])

    @staticmethod
    def crossover(self, chromosome1, chromosome2):
        assert (type(chromosome1) == Chromosome and type(chromosome2) == Chromosome)
        # TODO: stub
        return chromosome1

    def collect_nodes(self, original_tree):
        collector = NodeCollector()
        if collector is None:
            Log.ERROR(f'Failed to init NodeCollector')
            exit(1)

        collector.visit(original_tree)
        self.nodes = collector.get_nodes()

    def mutate(self, source, require_mutation=False):
        Log.INFO('Mutating source code...')
        new_source = None
        assert (type(source) == str)
        Log.INFO(f'Number of characters: {len(source)}')

        original_tree = ast.parse(source)

        Log.INFO('Collecting nodes.')
        self.collect_nodes(original_tree)
        
        count = 0
        Log.INFO('Beginning mutation process')
        while new_source is None or (require_mutation and self._num_mutations < 1):
            count += 1
            Log.INFO(f'Mutation iteration: {count}')

            # create a new tree from the original source code
            tree = ast.parse(source)

            # bug check to ensure AST can be converted back to raw source
            astor.to_source(tree)

            # visit the tree again, this time making mutations
            Log.INFO('Visiting tree with mutations turned on.')
            self.visit(tree)
            Log.INFO(f'Mutations made before parsing back to source: {self._num_mutations}')
            try:
                new_source = astor.to_source(tree)
            except AttributeError as e:
                Log.ERROR('Attribute Error occured while attempting to parse AST back to source.', urgency=1)
                Log.ERROR(f'Exception message: {e}', urgency=1)
                self._num_mutations = 0
                new_source = None
            except Exception as e:
                Log.ERROR('Unable to parse mutated AST back to source.', urgency=1)
                Log.ERROR(f'Exception message: {e}', urgency=1)
                self._num_mutations = 0
                new_source = None
            Log.INFO(f'Source is None: {new_source is None}, Require mutation: {require_mutation}, Mutations made: {self._num_mutations}')

        Log.INFO(f'Number of mutations made: {self._num_mutations}')
        # reset the mutators flags and namespace so it can be used again
        self._reset()
        
        return new_source

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
        self.size = 0

    def add_chromosome(self, source):
        chromosome = Chromosome(self, source=source)
        self.chromosomes.append(chromosome)
        self.size = len(self.chromosomes)

    def remove_chromosome(self, chromosome):
        assert(type(chromosome) == Chromosome)
        self.chromosomes.remove(chromosome)
        self.size = len(self.chromosomes)

    def get_fittest(self):
        if self.size == 0:
            return None
        return max(self.chromosomes, key=lambda x: x.fitness)

    def get_least_fit(self):
        if self.size == 0:
            return None
        return min(self.chromosomes, key=lambda x: x.fitness)

# base class that run a genetic algorithm on a single source code file with an associated unit test file
class GeneticSimulator():
    def __init__(self, source_file, test_file, repo, population_size=25, selection_size=10):
        Log.INFO(f'Initializing Genetic Simulator for source file {source_file}...')
        self.source_file = source_file
        self.source = None
        with open(os.path.abspath(__file__ + f'/../../../../repos/{repo}/src/{source_file}')) as f:
            self.source = f.read()
        self.test_file = test_file
        self.repo = repo
        self.population_size = population_size
        self.selection_size = selection_size
        self.population = None
        self.selection = None
        Log.INFO(f'Finished initializing Genetic Simulator for source file {source_file}.')

    def generate_starting_population(self):
        Log.INFO('Generating starting population...')
        # create a new empty population
        self.population = Population(self)

        # add population_size chromosomes to the population and randomly mutate them, 
        # leaving one unchanged and requiring all other be mutated at least once
        self.population.add_chromosome(self.source)
        mutator = Mutator(mutation_frequency=5)
        while(self.population.size < self.population_size):
            # mutate the source code
            # Mutator.mutate does not return until at least one mutation has been made when called with require_mutation=True
            mutated_source = mutator.mutate(self.source, require_mutation=True)
            self.population.add_chromosome(mutated_source)
        assert(self.population.size == self.population_size)
        Log.INFO('Finished generating starting population.')

    def get_fittest(self):
        return self.population.get_fittest()

    def get_least_fit(self):
        return self.population.get_least_fit()

    # method to check if the current population contains an optimal solution
    def has_optimal_solution(self):
        # TODO: stub
        pass

    # method to select a number of survivors from the current population for breeding
    def select(self):
        # TODO: stub
        pass
    
    # method to produce the next population with a selection from the current population
    def breed_next_generation(self):
        # TODO: stub
        pass
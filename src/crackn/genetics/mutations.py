import ast
import astor
import subprocess
import os
import random
import time
from crackn.parsing import bandit_parser as bp, unittest_parser
import crackn.settings as settings
import crackn.logging as Log

# helper class to instrument a unit test file so that it works with a modified version of the original source
class TestFileModifier(ast.NodeTransformer):
    def __init__(self, filename, uuid):
        super().__init__()
        self.filename = filename
        self.uuid = uuid

    # method to change import statments to use the modified version of the source code
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

        # require that either source code or an AST is provided
        if source is None and source_tree is None:
            raise Exception('Attempted to initialize a chromosome without source code or a source code AST.')
        self.source = source
        self.source_tree = source_tree

        if self.source is not None:
            Log.DEBUG('Initialized new chromosome from source')
            assert(type(self.source) == str)
        # if source code is not provided, generate it from the provided AST
        else:
            Log.DEBUG('Initialized new chromosome from AST')
            self.source = self.generate_source()

        # flag to track if a timeout occurs while running unit tests (indicating an error)
        self.timeout_occurred = False
        self.population = population

        # run the unit tests to gather information on the number of failing tests
        # tests should be run before the bandit report is run
        # this is because generating the bandit report is very expensive and we would like to check if the
        # unit tests fail and we can skip the bandit report altogether before attempting to generate it
        self.test_results = self.run_tests(population.simulation.test_file, population.simulation.repo)

        self.bandit_report = None
        if not (self.timeout_occurred or self.test_results.crashed or self.test_results.nran == 0):
            # generate a bandit report for information on security vulnerabilities in the given source code
            self.bandit_report = bp.BanditReport(source=source, auto_analyze=True, auto_parse=True)

        self.fitness = float('inf')

        # compute the fitness using the bandit report and test results
        self._compute_fitness()

        # check if this chromosome is a new local or global minimum and if so set the correct flags
        if self.fitness < self.population.simulation.best_fitness:
            self.population.simulation.best_fitness = self.fitness
            self.population.simulation.best_source = self.source

        if self.fitness < self.population.simulation.best_fitness_seen:
            self.population.simulation.best_fitness_seen = self.fitness
            self.population.simulation.best_source_seen = self.source

    def __eq__(self, other):
        return type(other) == type(self) and self.source == other.source and self.fitness == other.fitness

    def __ne__(self, other):
        return not self.__eq__(other)

    # make Chromosomes hashable so they can be stored in sets to improve performance
    def __hash__(self):
        return hash(repr(self))

    # method to compute the fitness of this chromosome based on the bandit static analysis report and the results of the unit tests
    def _compute_fitness(self):
        # if the unit tests or bandit report did not run, this chromosome should have infinite fitness (least fit)
        if self.bandit_report is None or self.bandit_report.skipped or self.timeout_occurred or self.test_results.crashed or self.test_results.nran == 0:
            self.fitness = float('inf')
        else:
            # the bandit report and test results will each contribute to the total fitness
            # a fitness of 0 represents an optimal solution
            bandit_fitness_contribution = None
            test_fitness_contribution = None

            # if bandit did not crash or skip any files and found no issues, it will not contribute to a higher fitness
            if len(self.bandit_report.issues) == 0:
                bandit_fitness_contribution = 0
            else:
                # initialize variables used to normalize bandit's contribution
                max_issue_rating = 0
                actual_issue_rating = 0

                for issue in self.bandit_report.issues:
                    # track the maximum possible issue rating
                    max_issue_rating += bp.Rating.get_weight(bp.Rating.HIGH) * bp.Rating.get_weight(bp.Rating.HIGH)

                    # track the current issue rating
                    actual_issue_rating += bp.Rating.get_weight(issue.confidence) * bp.Rating.get_weight(issue.severity)

                # calculate the average severity of an issue and multiply that by the total number of issues
                bandit_fitness_contribution = (float(actual_issue_rating) / max_issue_rating) * len(self.bandit_report.issues)

            # make the same calculation for the test cases
            test_fitness_contribution = (float(self.test_results.nfailing) / self.test_results.nran) * self.test_results.nfailing
            self.fitness = bandit_fitness_contribution + test_fitness_contribution
            if self.fitness == 0:
                self.population.simulation.optimal_solution_found = True

    # function to normalize the fitness of this chromosome with respect to the sum of fitnesses of the chromosomes in a population
    # not currently used in the GA algorithm but can be introduced in future updates
    def normalize_fitness(self, fitness_sum):
        self.fitness = float(self.fitness) / fitness_sum

    # helper method to generate source code if the chromosome was constructed from an AST
    def generate_source(self):
        Log.DEBUG('Generating source for chromosome from AST')
        assert(self.source_tree is not None)
        return astor.to_source(self.source_tree)

    # helper method to instrument the corresponding test code so that is runs with respect to this modified version
    # of the source code rather than using the original
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

    # helper method to store a file temporarily containing the modified source code this chromosome represents
    def create_source_file(self):
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{self.population.simulation.repo}')
        source_file = self.population.simulation.source_file
        with open(f'{file_path}/src/{source_file[:-3]}_{self.uuid}.py', 'w') as f:
            f.write(self.source)

    # helper method to delete any files created by the other methods in this class
    def cleanup_files(self):
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{self.population.simulation.repo}')
        test_file = self.population.simulation.test_file
        os.remove(f'{file_path}/test/{test_file[:-3]}_{self.uuid}.py')

        source_file = self.population.simulation.source_file
        os.remove(f'{file_path}/src/{source_file[:-3]}_{self.uuid}.py')

    # helper method to actually execute the test cases for this chromosome against its source
    def test(self, test_file, repo):
        file_path = os.path.abspath(__file__ + f'/../../../../repos/{repo}')
        current_path = os.path.abspath(os.getcwd())
        os.chdir(file_path)

        try:
            result = subprocess.run(['python3', f'test/{test_file}'], \
                                stdout=subprocess.PIPE, \
                                stderr=subprocess.STDOUT, timeout=2)
        except subprocess.TimeoutExpired:
            Log.WARNING(f'TimoutExpired exception occured while attempting to run test file {test_file}')
            self.timeout_occurred = True

        os.chdir(current_path)
        if self.timeout_occurred:
            return None

        return unittest_parser.UnittestParser.parse(result.stdout.decode('utf-8'))

    # method to generate all necessary temp files and execute the test suite corresponding the this chromosome's source
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

    # use the source code of this chromosome as a representation 
    # ensures unique representations and is used primarily for hashing
    def __repr__(self):
        return self.source

    # convenience method to pretty print a chromosome
    def short_repr(self):
        return f'Chrom. [fit={self.fitness}]'

# helper class used to visit an AST without mutating it and extract information about the nodes within
class NodeCollector(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.nodes = dict()

    def get_nodes(self):
        return self.nodes

    # add the node to our dictionary of nodes
    def visit_any_node(self, node, node_type):
        Log.DEBUG(f'Visiting node {node} with mutations turned off.')
        if node_type in self.nodes:
            self.nodes[node_type].append(node)
        else:
            self.nodes[node_type] = [node]
        self.generic_visit(node)

    # define the types of nodes we want to track here
    def visit_Name(self, node):
        self.visit_any_node(node, ast.Name)

    def visit_Call(self, node):
        self.visit_any_node(node, ast.Call)

# class to mutate source code by converting it to an AST and traversing the nodes
class Mutator(ast.NodeTransformer):
    def __init__(self, mutation_frequency=1):
        super().__init__()
        # define a mutation frequency as how likely we are to mutatate any given node
        assert(1 <= mutation_frequency <= 100)
        self.mutation_frequency = mutation_frequency
        self.nodes = None
        self._num_mutations = 0

    # helper method containing logic to decide whether or not to mutate a given node
    def visit_any_node(self, node, node_type):
        Log.DEBUG(f'Visiting {node_type} node')
        if self.should_mutate():
            Log.DEBUG(f'Mutating node {node}')
            self._num_mutations += 1
            selected_mutation = self.select_random_mutation()
            Log.DEBUG(f'Selected mutation: {selected_mutation}')
            return selected_mutation(node)
        else:
            Log.DEBUG('Returning original node.')
            return node

    # define the nodes we would like to potentially mutate here
    def visit_Name(self, node):
        return self.visit_any_node(node, ast.Name)

    def visit_Call(self, node):
        return self.visit_any_node(node, ast.Call)

    # helper method to decide if a node should mutate or not
    def should_mutate(self):
        if random.randint(1, 100) <= self.mutation_frequency:
            Log.DEBUG(f'Choosing to mutate.')
            return True
        Log.DEBUG(f'Choosing not to mutate.')
        return False

    # POSSIBLE MUTATION FUNCTIONS
    # mutate by deleting the node altogether
    def delete_node(self, node):
        return None

    def replace_node_with_same_type(self, node):
        # replace the node with another node in the tree of the same type if one exists, else delete the node
        # Note: if the current node is the only node seen of its type this function will always delete it
        if type(node) in self.nodes:
            return random.choice(self.nodes[type(node)])
        return None

    # replace the node with another node of any type
    def replace_node_with_any_type(self, node):
        return random.choice(self.nodes[random.choice(list(self.nodes))])

    # replace the node with a call to a true random number generator
    # this mutation is used primarily for testing and does not necessarily represent a good mutation
    def replace_node_with_random(self, node):
        Log.DEBUG(f'Replacing node with call to random number generator.')
        return ast.Call(func=ast.Attribute(value=ast.Name(id='int'), attr='from_bytes'),
                        args=[ast.Call(func=ast.Attribute(value=ast.Name(id='os'), attr='urandom'), args=[ast.Num(n=1)], keywords=[])],
                        keywords=[ast.keyword(arg='byteorder', value=ast.Str(s='big'))])

    # END OF POSSIBLE MUTATION FUNCTIONS
    # TODO: add more mutations

    # method to select a mutation randomly from the available mutations
    # specific mutations can be enabled/disabled by listing them here or removing them
    # TODO: allow these mutations to be set from the command line
    def select_random_mutation(self):
        return random.choice([self.delete_node,
                              self.replace_node_with_same_type, 
                              self.replace_node_with_any_type, 
                              self.replace_node_with_random])

    # method to collect information on the nodes in the tree before modifying them
    def collect_nodes(self, original_tree):
        # initialize a NodeCollector which will be used to visit the tree
        collector = NodeCollector()
        if collector is None:
            Log.ERROR(f'Failed to init NodeCollector')
            exit(1)

        # tell the NodeCollector to visit the tree, then get its dictionary of nodes
        collector.visit(original_tree)
        self.nodes = collector.get_nodes()

    # this is the primary method of the Mutator class
    # it is used to convert a given piece of source code to an AST,
    # make changes/mutations to the AST, then convert it back to source code
    def mutate(self, source, require_mutation=False):
        Log.DEBUG('Mutating source code...')
        new_source = None
        assert (type(source) == str)
        Log.DEBUG(f'Number of characters: {len(source)}')

        original_tree = None
        # attempt to parse the source code to an AST
        # if this fails, the source code is not valid python, so return the original source without mutating
        # this is because it is highly unlikely any mutations will fix any errors in the code, and broken source code 
        # will cause the resulting chromosome to have a fitness of inf
        try:
            original_tree = ast.parse(source)
        except SyntaxError:
            return source

        # collect the nodes from the tree in advance so we can use them for substitutions later
        Log.DEBUG('Collecting nodes.')
        self.collect_nodes(original_tree)
        
        # count the number of mutations in case we want to enforce that at least k mutations be made
        count = 0
        Log.DEBUG('Beginning mutation process')

        # continue looping as long as our new source code is not yet valid or we have not made enough mutations
        while new_source is None or (require_mutation and self._num_mutations < 1):
            count += 1
            Log.DEBUG(f'Mutation iteration: {count}')

            # create a new tree from the original source code
            # TODO: optimize
            tree = ast.parse(source)

            # visit the tree again, this time making mutations
            Log.DEBUG('Visiting tree with mutations turned on.')
            # note that no explicit mutations are being made here, as those are mode inside of the visit_[Node] methods
            self.visit(tree)
            Log.DEBUG(f'Mutations made before parsing back to source: {self._num_mutations}')

            # attempt to convert the AST back to source
            # if it cannot be done then reset to the original source code and try mutating again
            try:
                new_source = astor.to_source(tree)
            except AttributeError as e:
                Log.DEBUG('Attribute Error occured while attempting to parse AST back to source.')
                Log.DEBUG(f'Exception message: {e}')
                self._num_mutations = 0
                new_source = None
            except Exception as e:
                Log.DEBUG('Unable to parse mutated AST back to source.')
                Log.DEBUG(f'Exception message: {e}')
                self._num_mutations = 0
                new_source = None
            Log.DEBUG(f'Source is None: {new_source is None}, Require mutation: {require_mutation}, Mutations made: {self._num_mutations}')

        Log.DEBUG(f'Number of mutations made: {self._num_mutations}')
        # reset the mutators flags and namespace so it can be used again
        self._reset()
        
        return new_source

    # convenience method which allows one mutator to be reset and used again for a different piece of source code
    def _reset(self):
        self._mutate = False
        self._names = set()
        self._num_mutations = 0

# a class representing a collection of chromosomes
class Population():
    def __init__(self, simulation):
        # TODO: stub
        self.simulation = simulation
        self.chromosomes = set()
        self.size = 0

    # helper method to add a chromosome from a piece of source code
    def _add_chromosome_source(self, source):
        chromosome = Chromosome(self, source=source)
        self.chromosomes.add(chromosome)

    # helper method to add a chromosome from an existing chromosome
    def _add_chromosome_existing(self, chromosome):
        new_chromosome = Chromosome(self, source=chromosome.source)
        self.chromosomes.add(new_chromosome)

    # add a chromosome to the population via either source code or an existing chromosome
    def add_chromosome(self, seed):
        seed_type = type(seed)
        assert(seed_type in (Chromosome, str))

        # determine the type of seed and call the correct helper method
        if seed_type == Chromosome:
            self._add_chromosome_existing(seed)
        else:
            self._add_chromosome_source(seed)
        self.size += 1

    # method to remove a chromosome from the population
    def remove_chromosome(self, chromosome):
        assert(type(chromosome) == Chromosome)
        # don't allow any chromosomes to be removed if there are no chromosomes in the population
        if self.size == 0:
            Log.WARNING('Tried to remove a chromosome from an empty population')
            return
        self.chromosomes.remove(chromosome)
        self.size -= 1

    # method which returns the chromosome with the best fitness (lowest)
    def get_fittest(self):
        if self.size == 0:
            return None
        return min(self.chromosomes, key=lambda x: x.fitness)

    # method which returns the chromosome with the worst fitness (highest) not including chromosomes with fitness infinity
    def get_least_fit(self):
        if self.size == 0:
            return None
        return max([x for x in self.chromosomes if x.fitness != float('inf')], key=lambda x: x.fitness)

# base class that run a genetic algorithm on a single source code file with an associated unit test file
class GeneticSimulator():
    def __init__(self, source_file, test_file, repo, population_size=50, selection_size=15):
        Log.INFO(f'Initializing Genetic Simulator for source file {source_file}...')
        Log.INFO(f'Population Size: {population_size}')
        Log.INFO(f'Selection Size: {selection_size}')

        # initialize basic class variables (public)
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

        # the best fitness and the associated source code for this population
        self.best_fitness = float('inf')
        self.best_source = None

        # the best fitness and the associated source code for all populations seen
        self.best_fitness_seen = float('inf')
        self.best_source_seen = None

        # variables used for simulating continuously until an optimal is found
        self.max_generations = 100
        self.max_stagnant_generations = 5
        self.max_resets = 3

        # variables for simulating
        self.optimal_solution_found = False
        self.generations = 0

        Log.INFO(f'Finished initializing Genetic Simulator for source file {source_file}.')

    # method to generate a random starting population from scratch
    # this can be used at the beginning of the lifecycle of the simulation
    # or as a reset of the simulation gets stuck at a local optimum during prolonged simulation
    def generate_starting_population(self):
        Log.INFO('Generating random population.')
        # create a new empty population
        self.population = Population(self)

        # add population_size chromosomes to the population and randomly mutate them, 
        # leaving one unchanged and requiring all other be mutated at least once
        chromosome = Chromosome(self.population, source=self.source)
        Log.DEBUG(f'Original source code for file {self.source_file} has a fitness of {chromosome.fitness}.')

        self.population.add_chromosome(chromosome)
        mutator = Mutator(mutation_frequency=5)
        while(self.population.size < self.population_size):
            # mutate the source code
            # Mutator.mutate does not return until at least one mutation has been made when called with require_mutation=True
            mutated_source = mutator.mutate(self.source, require_mutation=True)
            self.population.add_chromosome(mutated_source)
        assert(self.population.size == self.population_size)

        Log.INFO('Finished generating starting population.')

    # convenience wrapper method of the Population.get_fittest method
    def get_fittest(self):
        return self.population.get_fittest()

    # convenience wrapper method of the Population.get_least_fit method
    def get_least_fit(self):
        return self.population.get_least_fit()

    # method to check if the current population contains an optimal solution
    def has_optimal_solution(self):
        for chromosome in self.population.chromosomes:
            if chromosome.fitness == 0:
                return True
        return False

    # method to normalize the fitness values for the current population such that all fitness
    # values fall between 0 and 1, and the sum of all fitness values is 1
    def normalize_fitness_values(self):
        # get the sum of all the fitness values
        fitness_sum = sum([x.fitness for x in self.population.chromosomes])
        for chromosome in self.population.chromosomes:
            # tell the chromosome to normalize itself given the fitness sum
            chromosome.normalize_fitness(fitness_sum)

    # method to select a number of survivors from the current population for breeding
    def select_survivors(self):
        population = self.population
        rounds = self.selection_size
        survivors = Population(self)

        # iterate for the given number of rounds
        while survivors.size < rounds:
            # select a random tournament size
            tournament_size = random.randint(2, population.size // 2)
            assert(tournament_size < population.size)
            # select random competitors
            try:
                competitors = random.sample(population.chromosomes, tournament_size)
            except ValueError as e:
                Log.ERROR(f'Population size ({population.size}) is less than tournament size ({tournament_size})')
                Log.ERROR(f'{e}')
                exit(1)

            # choose the competitor with the highest fitness value
            winner = None
            for competitor in competitors:
                if winner is None or competitor.fitness < winner.fitness:
                    winner = competitor
            survivors.add_chromosome(winner)
            # remove the winner from the population so they cannot be selected again
            population.remove_chromosome(winner)
        
        assert(survivors.size == rounds)
        self.selection = survivors
    
    # helper method to randomly select two parents to mate
    def _select_parents(self):
        assert(self.selection is not None)
        tuple_chromes = tuple(self.selection.chromosomes)
        # randomly choose both parents
        parent1, parent2 = random.choice(tuple_chromes), random.choice(tuple_chromes)
        # keep randomly choosing the second parent if it is the same as the first parent
        while parent2 is parent1:
            parent2 = random.choice(tuple_chromes)
        assert(parent1 is not parent2)
        return parent1, parent2

    # method to combine the solutions of two parent chromosomes to form a child chromosome
    # this is accomplished by picking an inflection point in the code, for example, halfway through a file,
    # and then combining the first parent's data up to that infection point with the second parent's data
    # from that inflection point to the end
    def crossover(self, parent1, parent2):
        assert(type(parent1) == type(parent2) == Chromosome)
        source1_lines = parent1.source.split('\n')
        source2_lines = parent2.source.split('\n')
        line_count = min([len(source1_lines), len(source2_lines)])

        # choose a random inflection point
        inflection_point = random.randint(1, line_count-1)

        # use single point crossover for now
        # choose which partial source code should come first
        first = random.choice([source1_lines, source2_lines])
        second = source2_lines if first == source1_lines else source1_lines

        new_source = '\n'.join(first[:inflection_point]) + '\n'.join(second[inflection_point:])
        return new_source

    # method that combines several helper methods to produce a single child chromsome from two parents
    def produce_offspring(self, parent1, parent2):
        # get a random int that acts as a percentage
        percent = random.randint(0, 100)
        # 70% of the time perform crossover of the two parents
        if percent <= 70:
            child_source = self.crossover(parent1, parent2)
        # 30% of the time choose one parent to pass on their genes to the child
        else:
            child_source = random.choice((parent1, parent2)).source
        mutated_source = Mutator().mutate(child_source)
        return mutated_source

    # method to produce the next population with a selection from the current population
    def breed_next_generation(self):
        next_population = Population(self)

        while next_population.size < self.population_size:
            parent1, parent2 = self._select_parents()
            child_source = self.produce_offspring(parent1, parent2)
            next_population.add_chromosome(Chromosome(self.population, source=child_source))

        self.population = next_population
        self.selection = None

    # helper method to simulate a single generation
    # not generally called directly. This will usually be called by either sim_n_generations or sim_until_optimal_found
    def sim_one_generation(self):
        if self.optimal_solution_found:
            Log.WARNING('Optimal solution already found. Reset to run more simulations', urgency=3)
            return

        # temporarily do not normalize fitness values
        # this is throwing off the algorithm because some chromosomes have a fitness of infinity
        #self.normalize_fitness_values()

        # select a number of survivors from the current population to breed the next population
        # currently uses tournament select as the selection algorithm
        self.select_survivors()

        # breed the next generation using the survivors selected
        self.best_fitness = float('inf')
        self.breed_next_generation()
        self.generations += 1

    # method to simulate for n generations
    # primarily used for testing (need to simulate for more than one gen but don't want to wait for the entire algorithm to run)
    def sim_n_generation(self, n):
        print()
        Log.INFO(f'Beginning simulation over {n} generations.')
        print()
        start = time.time()
        time_sum = 0

        # loop n times
        for _ in range(n):
            gen_start = time.time()
            Log.INFO(f'Simulating generation {self.generations}', urgency=3)

            # simulate a single generation
            self.sim_one_generation()
            gen_end = time.time()
            time_sum += gen_end - gen_start
            Log.INFO(f'Finished simulating generation {self.generations - 1} in {round(gen_end - gen_start, 2)} seconds (avg {round(time_sum/self.generations, 2)}s)')
            Log.INFO(f'Current running time: {time.time() - start}s')
        Log.INFO(f'Simulated {n} generations in {time.time() - start} seconds.', urgency=3)

        # output our best found solution to a file
        self.output_final_files()

    # method to continue simulating until an optimal solution is found or no progress has been made for a significant amount of time
    def sim_until_optimal_found(self):
        # if we have already found an optimal solution there is no need to simulate again
        # this will not happen currently but the check is here for future additions and extensions of the tool
        if self.optimal_solution_found:
            Log.WARNING('Optimal solution already found. Reset to run another simulation')
            return

        # initialize some variables to track our simulation's progress
        best_fitness_seen = float('inf')
        stagnant_generations = 0
        resets = 0

        start = time.time()
        # continue to loop while we have not found a solution
        while not self.optimal_solution_found:
            # simulate a single generation
            self.sim_one_generation()

            # output some useful data for the user to view
            avg_fitness, nsubjects = self.average_fitness()
            Log.INFO(f'Generations simulated: {self.generations}')
            Log.INFO(f'Current Average Fitness: {avg_fitness} ({nsubjects} subjects)')
            Log.INFO(f'Current Best Fitness: {self.best_fitness}')
            Log.INFO(f'Time Elapsed: {time.time() - start}s')

            # if we have simulated for longer than the specified max number of generations we should stop iterating
            # max_generations can be set manually in GeneticSimulator's constructor
            # TODO: make max_generations able to be set from the command line
            if self.generations >= self.max_generations:
                Log.WARNING('Optimal solution unlikely...', urgency=3)
                Log.WARNING('Consider modifying breeding/mutation technique.', urgency=3)
                break

            # check if we have seen a new best fitness update our variables
            if self.best_fitness < best_fitness_seen:
                best_fitness_seen = self.best_fitness
                stagnant_generations = 0
            else:
                # otherwise note that another generation has passed without seeing an update
                stagnant_generations += 1

            # if it has been long enough since we have seen a new best fitness, try to reset with a new starting population
            if stagnant_generations > self.max_stagnant_generations:
                if resets < self.max_resets:
                    self.generate_starting_population()
                    resets += 1
                    best_fitness_seen = float('inf')
                    stagnant_generations = 0
                else:
                    Log.WARNING('Reached max number of stagnant generations or random resets. Stopping simulation.')
                    break

        self.optimal_solution_found = True
        self.output_final_files()

    # helper method to output the most fit chromosome found by the algorithm to a file for human viewing
    def output_final_files(self):
        filename = f'{self.source_file[:-3]}_mutated.py'
        repo_path = os.path.abspath(__file__ + f'/../../../../repos/{self.repo}/results')
        os.mkdir(repo_path)
        Log.INFO(f'\nWriting final chromosome to {filename}')
        with open(f'{repo_path}/{filename}', 'w') as f:
            f.write(self.best_source_seen)

    # helper method to comput the average fitness of the current population not including chromosomes with a fitness of infinity
    def average_fitness(self):
        fitness_sum = [x.fitness for x in self.population.chromosomes if x.fitness != float('inf')]
        nsubjects = len(fitness_sum)
        # return the average fitness, as well as the number of subjects whose fitnesses were used to compute this average
        return sum(fitness_sum)/nsubjects, nsubjects

    # return a string representation of the simulator
    def __repr__(self):
        avg_fitness, nsubjects = self.average_fitness()
        return    f'GeneticSimulator for {self.source_file}\n' + \
                  f'===========================================\n' + \
                  f'Population Size: {self.population.size}\n' + \
                  f'Selection Size: {self.selection_size}\n' + \
                  f'Average Fitness: {avg_fitness} ({nsubjects} subjects)\n' + \
                  f'Best Fitness: {self.best_fitness}\n'
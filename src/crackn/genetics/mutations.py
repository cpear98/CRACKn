import ast
import astor
from crackn.parsing import bandit_parser

class Chromosome():
    def __init__(self, source=None, source_tree=None):
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
        self.bandit_report = bandit_parser.BanditReport(source=source, auto_analyze=True, auto_parse=True)

    def __eq__(self, other):
        # TODO: stub
        pass

    def __ne__(self, other):
        # TODO: stub
        pass

    def _determine_fitness(self):
        # TODO: stub
        pass

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

class Mutator():
    def __init__(self):
        # TODO: stub
        pass

    def crossover(self, chromosome1, chromosome2):
        assert (type(chromosome1) == Chromosome and type(chromosome2) == Chromosome)
        # TODO: stub
        return chromosome1

    def mutate(self, chromosome):
        assert (type(chromosome) == Chromosome)
        # TODO: stub
        return chromosome

class Population():
    def __init__(self):
        # TODO: stub
        self.chromosomes = set()

    
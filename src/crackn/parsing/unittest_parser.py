class UnittestResults():
    def __init__(self, crashed, nran, npassing, nfailing):
        self.crashed = crashed
        self.nran = nran
        self.npassing = npassing
        self.nfailing = nfailing

class UnittestParser():
    @staticmethod
    def parse(string):
        results = string.split('\n')
        end_results = results[len(results)-3:]
        num_ran = int(end_results[0].split()[1])
        num_failed = int(end_results[2][-2])
        return UnittestResults(False, num_ran, num_ran - num_failed, num_failed)
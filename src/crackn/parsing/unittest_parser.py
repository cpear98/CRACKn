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
        nran, nfailed = 0, 0
        for line in results:
            line = line.split()
            if len(line) == 0:
                pass
            elif line[0] == 'Ran':
                nran = int(line[1])
            elif line[0] == 'FAILED':
                nfailed = int(line[1][-2])
        return UnittestResults(False, nran, nran - nfailed, nfailed)
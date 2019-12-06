from enum import Enum
import subprocess
import os
import tempfile
import crackn.logging as Log

# enum values used for issue severity and confidence
class Rating(Enum):
    UNDEFINED = 0,
    LOW = 1,
    MEDIUM = 2,
    HIGH = 3

    @staticmethod
    def get_weight(rating):
        assert(type(rating) == Rating)
        weight = rating.value if type(rating.value) == int else rating.value[0]
        return weight

    @classmethod
    def from_string(self, string):
        rating_dict = {'undefined': self.UNDEFINED, 'low': self.LOW, 'medium': self.MEDIUM, 'high': self.HIGH}
        lower = string.lower()
        if lower in rating_dict:
            return rating_dict[lower]
        return None

    @classmethod
    def to_string(self, rating):
        rating_dict = {self.UNDEFINED: 'Undefined', self.LOW: 'Low', self.MEDIUM: 'Medium', self.HIGH: 'High'}
        return rating_dict[rating]

class Location():
    def __init__(self, full_path):
        self.file = None
        self.line_number = None
        self._from_path(full_path)

    def _from_path(self, path):
        split = path.split(':')
        self.file = split[0]
        self.line_number = int(split[1])

class Issue():
    def __init__(self, issue_id=None, description=None, severity=None, confidence=None, location=None, lines=None):
        self.issue_id = issue_id
        self.description = description
        self.severity = severity
        self.confidence = confidence
        self.location = location

        if lines is not None:
            self._from_lines(lines)

    def _from_lines(self, lines):
        # line 1 contains the issue number and description
        line_one = lines[0].split()
        self.issue_id = line_one[2]
        # check that the issue number was grabbed correctly
        assert(self.issue_id[0] == '[' and self.issue_id[-1] == ']')
        # then remove the brackets
        self.issue_id = self.issue_id[1:-1]

        self.description = ' '.join(line_one[3:])

        # line 2 contains the severity and confidence ratings
        line_two = lines[1].split()
        self.severity = Rating.from_string(line_two[1])
        self.confidence = Rating.from_string(line_two[3])

        # line 3 contains the location of the vulnerability
        line_three = lines[2].split()
        self.location = Location(line_three[1])

        #lines 4 through are not used for now

    def __repr__(self):
        string = ''
        string += '<Issue object>\n'
        string += f'\tIssue ID: {self.issue_id}\n'
        abbreviated_desc = self.description[:60] + '...' if len(self.description) > 63 else self.description
        string += f'\tDescription: {abbreviated_desc}\n'
        string += f'\tSeverity: {Rating.to_string(self.severity)}\n'
        string += f'\tConfidence: {Rating.to_string(self.confidence)}\n'
        string += f'\tFile: {self.location.file}\n'
        string += f'\tLine number: {self.location.line_number}'
        return string

# class to parse the string output of bandit
class BanditReport():
    def __init__(self, source=None, bandit_report=None, auto_analyze=False, auto_parse=False):
        if source is None and bandit_report is None:
            raise Exception('Attempted to initialize a bandit report with no source code or bandit output.')

        self.report = None

        if bandit_report is None:
            # sets self.report
            self.source = source
            if auto_analyze:
                self.analyze()
        else:
            self.report = bandit_report

        self.issues = None
        self.lines_scanned = None
        self.lines_skipped = None
        self.issues_by_severity = {Rating.UNDEFINED: None, Rating.LOW: None, Rating.MEDIUM: None, Rating.HIGH: None}
        self.issues_by_confidence = {Rating.UNDEFINED: None, Rating.LOW: None, Rating.MEDIUM: None, Rating.HIGH: None}
        self.skipped = False

        if auto_parse:
            self.parse()

    # potential opportunity to optimize
    def analyze(self):
        # create a temporary file and write the source code to it
        f = tempfile.NamedTemporaryFile(mode='w', delete=False)
        try:
            f.write(self.source)
            f.close()
            # invoke bandit to analyze the source code
            self.report = subprocess.run(['bandit', '-r', f.name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10.0).stdout.decode('utf-8')
        finally:
            os.remove(f.name)

    # not a significant optimization opportunity
    def parse(self):
        self.issues = set()
        strings = self.report.split('\n')
        for i in range(len(strings)):
            line = strings[i].split()
            # issues always start with string literal ">>"
            if len(line) > 0 and line[0] == '>>':
                # an issue in the bandit report spans 7 lines
                self.issues.add(Issue(lines=strings[i:i+7]))
            elif len(line) > 0 and ' '.join(line[:2]) == 'Files skipped' and line[2] != '(0):':
                self.skipped = True
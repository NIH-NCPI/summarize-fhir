"""
Base class for all summary classes
"""

from collections import defaultdict
from copy import deepcopy
import re

# Whistle denotes data-dictionary components using /data-dictionary/
# We shouldn't return these unless they are the only code found
dd_filter = re.compile("\/data-dictionary\/")

class NoValidCode(Exception):
    def __init__(self):
        super().__init__(self.message())

    def message(self):
        return "No valid code found"


def ChooseCode(coding):
    "Remove DD codes and sort by code, returning the first in case "
    "conditions with the same codes aren't ordered the same"
    if len(coding) == 1:
        return coding[0]
    
    valid_matches = {}
    codes = []
    for code in coding:
        if dd_filter.search(code['system']) is None:
            codes.append(code['code'])
            valid_matches[code['code']] = code

    if len(codes) > 0:
        return valid_matches[sorted(codes)[0]]

    raise NoValidCode()

class Summary:
    def __init__(self):
        # domain => code => count
        self.counts = defaultdict(lambda: defaultdict(lambda: 0))

        # We'll need these observed codes to build the components
        # domain => code => coding
        self.observed_codes = defaultdict(dict)

        self.resource_count = 0

    def BuildSummaryObservations(self, population):
        # The derived classes should have overridden this function
        assert(False)

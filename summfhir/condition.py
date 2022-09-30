"""
Summarize conditions associated with a select group of patients
"""

from summfhir import MetaTag
from summfhir.summary import Summary, ChooseCode
from summfhir.terms import VAR_SUM_CC, COUNT
from copy import deepcopy


class Condition(Summary):
    def __init__(self, conditions):
        super().__init__()

        # Let's grab some identifier details from the first resource as a 
        # starting point for a system to use inside each of our summary objects
        self.identifier_system = conditions[0]['identifier'][0]['system'] + "/summary"

        for resource in conditions:
            self.add_resource(resource)

    def add_resource(self, resource):
        # Skip any that have a verificationStatus that isn't confirmed
        verstat = "confirm"
        if "verificationStatus" in resource:
            verstat = resource['verificationStatus']['coding'][0]['code']

            if verstat not in self.observed_codes:
                self.observed_codes[verstat] = resource['verificationStatus']

        cc = ChooseCode(resource['code']['coding'])
        if cc is not None:
            code = cc['code']
            if code not in self.observed_codes:
                self.observed_codes[code] = deepcopy(resource['code'])
                
            self.counts[code][verstat] += 1

    def return_text_results(self):        
        result = f""

        for code in sorted(self.counts.keys()):
            display = self.observed_codes[code]['coding'][0]['display']
            result += f"  {code}: {self.counts[code]['confirmed']} ({display})\n"

        return result

    def BuildSummaryObservations(self, population):
        # There will be one observation per code
        summaries = []

        observation_base = {
            "resourceType": "Observation",
            "meta": {
                "tag": MetaTag()
            },
            "status": "final",
            "code": VAR_SUM_CC,
        }

        for code in sorted(self.counts.keys()):
            summary = deepcopy(observation_base)

            # Let's differentiate each of our summaries by population and
            # the underlying source of the data (race, eth, etc)
            summary['identifier'] = [{
                "system": self.identifier_system,
                "value": f"{population.id}.{code}"
            }]

            summary['valueCodeableConcept'] = self.observed_codes[code]
            summary['subject'] = {
                "reference": f"Group/{population.id}"
            }
            summary["component"] = [{
                "code": COUNT.as_coding(),
                "valueInteger": self.counts[code]['confirmed']
            }]

            summaries.append(summary)

        return summaries

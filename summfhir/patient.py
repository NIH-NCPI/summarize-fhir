"""
Summarize the demographics for a set of patient resources

Current sumaries include: 
    Sex
    Race
    Ethnicity
"""

from summfhir import AddCoding, MetaTag
from summfhir.summary import Summary, ChooseCode
from summfhir.terms import VAR_SUM_CC, MISSING, ETHNICITY, RACE, SEX
from copy import deepcopy
import pdb 

System = {
    "race": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
    "ethnicity": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
}

DemoCodings = {
    "race": RACE,
    "ethnicity": ETHNICITY,
    "gender": SEX
}


def GetProperExtension(extensions, url):
    """Work through the extensions looking for a matching URL. Return Text if """
    """none match"""

    text_option = {}
    for ext in extensions:
        if ext['url'] == url:
            return ext
        if ext['url'] == 'text':
            text_option = ext
    return text_option

class Patient(Summary):
    def __init__(self, resources):
        super().__init__()

        # Let's grab some identifier details from the first resource as a 
        # starting point for a system to use inside each of our summary objects
        self.identifier_system = resources[0]['identifier'][0]['system'] + "/summary"

        self.resource_count = len(resources)
        for resource in resources:
            self.add_resource(resource)

    def add_resource(self, resource):
        for extn in resource['extension']:
            if extn['url'] == System['race']:
                
                race_ext = GetProperExtension(extn['extension'], "ombCategory")
                if 'valueCoding' in race_ext:
                    race = race_ext['valueCoding']['display']
                    race_coding = race_ext['valueCoding']
                else:
                    race = race_ext['valueString']
                    race_coding = race_ext
                    
                if race not in self.observed_codes:
                    self.observed_codes['race'][race] = race_coding

                self.counts['race'][race] += 1

            elif extn['url'] == System['ethnicity']:
                eth_ext = GetProperExtension(extn['extension'], "ombCategory")
                if 'valueCoding' in race_ext:
                    eth = eth_ext['valueCoding']['display']
                    eth_coding = eth_ext['valueCoding']
                else:
                    eth = eth_ext['valueString']
                    eth_coding = eth_ext

                if eth not in self.observed_codes:
                    self.observed_codes['ethnicity'][eth] = eth_coding

                self.counts['ethnicity'][eth] += 1
        
        if 'gender' in resource:
            gender = resource['gender']

            if gender not in self.observed_codes['gender']:
                self.observed_codes['gender'][gender] = AddCoding(gender, gender.capitalize(), "http://hl7.org/fhir/administrative-gender")

            self.counts['gender'][resource['gender']] += 1

    def return_text_results(self):        
        result = ""
        for code in self.counts.keys():
            result += f"  {code}:\n"
            total = 0
            for var in sorted(self.counts[code].keys()):
                total += self.counts[code][var]
                realcode = self.observed_codes[code][var]['code']
                if var != realcode:
                    realcode = f"({realcode})"
                else:
                    realcode = ""
                result += f"    {var} {realcode}: {self.counts[code][var]}\n"
            result += f"    missing: {self.resource_count - total}\n"

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
            "subject": {
                "reference": f"Group/{population.id}"
            },
            "component": []
        }

        for code in sorted(self.counts.keys()):
            summary = deepcopy(observation_base)

            # Let's differentiate each of our summaries by population and
            # the underlying source of the data (race, eth, etc)
            summary['identifier'] = [{
                "system": self.identifier_system,
                "value": f"{population.id}.{code}"
            }]
            summary['valueCodeableConcept'] = DemoCodings[code].as_coding()
            summary['valueCodeableConcept']['text'] = code


            total = 0
            for var in sorted(self.counts[code].keys()):
                total += self.counts[code][var]
                summary['component'].append({
                    "code": {
                        "coding": [
                            self.observed_codes[code][var]
                        ], 
                        "text": var
                    },
                    "valueInteger": self.counts[code][var]
                })


            summary['component'].append({
                "code": MISSING.as_coding(),
                "valueInteger": self.resource_count - total
            })

            summaries.append(summary)
        return summaries
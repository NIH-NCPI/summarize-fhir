"""
summarize the variables from the Observation (with components) resources
"""

from summfhir import (AddCoding, 
                    OfficialIdentifier, 
                    GetValue, 
                    GetInputClient, 
                    GetOutputClient,
                    Coding,
                    MetaTag)

from summfhir.summary import Summary

import sys
import pdb 
from collections import defaultdict

from summfhir.terms import VAR_SUM_CC, MISSING, COUNT, MEAN
from copy import deepcopy


source_data_code = "74468-0"

class ComponentDataParser:
    def __init__(self, resource):
        """Initialize the parser with the expected number of observations """
        """so that we can properly account for the number of missing"""
        self.n = 0

        # Track the actual code associated with this variable
        # This includes code, display and system
        coding = resource['code']
        self.coding = coding

        self.identifier = resource['identifier'][0]
        self.identifier['system'] = self.identifier['system'].replace("/observationdefinition", "/summary/observation")

        # The number of records we've encountered along the way associated
        # with this particular variable
        self.observed = 0

        self.mismatched_keys = defaultdict(int)
    @property
    def code(self):
        return SelectKeyCode(self.coding)

    def ParseData(self, component):
        sys.stderr.write(f"No ParseData function found for {self.__class__.__name__}")
        sys.exit(1)

    def note_mismatched(self, code):
        self.mismatched_keys[code] += 1

    def list_mismatched_counts(self):
        if len(self.mismatched_keys) > 0:
            counts = "      Not in DD:\n"

            for key in self.mismatched_keys:
                counts += f"        {key}: {self.mismatched_keys[key]}\n"
            return counts
        return ""

class ComponentStringParser(ComponentDataParser):
    def __init__(self, resource):
        super().__init__(resource)

        self.unique_values = set()

    def ParseData(self, component):
        self.unique_values.add(component['valueString'])
        self.observed += 1

    def return_text_results(self):       
        unique_count = len(self.unique_values)
        return f"""      Unique Values: {unique_count}
      missing: {self.n - self.observed}\n"""

    def BuildComponents(self):
        unique_count = len(self.unique_values)
        component = [{
            "code": COUNT.as_coding(),
            "valueInteger": unique_count,
        }, {
            "code": MISSING.as_coding(),
            "valueInteger": self.n - self.observed
        }
        ]

        component[0]["code"]["text"] = "Unique Values"

        return component


class ComponentValueSetParser(ComponentDataParser):
    def __init__(self, resource):
        super().__init__(resource)

        self.valid_values = {}
        self.value_counts = {}
        client = GetInputClient()

        self.vsref = resource['validCodedValueSet']['reference']
        result = client.get(f"{self.vsref}/$expand")

        if result.success():
            # We know ahead of time every possible category that might be 
            # encountered, based on the VS. So, we'll set each to zero
            # just to provide a comprehensive report including those that
            # are never encountered
            for newcoding in result.entries[0]['expansion']['contains']:
                coding = Coding(resource=newcoding)
                self.valid_values[coding.code] = coding
                self.value_counts[coding.code] = 0

    def extract_code_from_component(self, component):
        for coding in component['valueCodeableConcept']['coding']:
            code = coding['code']
            if code in self.valid_values and coding['system'] == self.valid_values[code].system:
                return coding
        return None

    def ParseData(self, component):
        if 'valueString' in component:
            self.note_mismatched(component['valueString'])
        elif 'valueCodeableConcept' in component:
            try:
                self.value_counts[self.extract_code_from_component(component)['code']] += 1
            except:
                if 'text' in component['valueCodeableConcept']:
                    self.note_mismatched(component['valueCodeableConcept']['text'])
                else:
                    print(component)
                    print(", ".join(sorted(self.value_counts.keys())))
                    pdb.set_trace()
        else:
            print("Not sure what to do with this one:")
            print(component)
            pdb.set_trace()

    def return_text_results(self):        
        result = f""

        total = 0
        for code in self.value_counts.keys():
            result += f"      {code}: {self.value_counts[code]}\n"
            total += self.value_counts[code]
        result += self.list_mismatched_counts()
        result += f"      missing: {self.n - total}\n"

        return result

    def BuildComponents(self):
        component = []
        
        total = 0
        for code in sorted(self.value_counts.keys()):
            total += self.value_counts[code]
            component.append({
                "code": self.valid_values[code].as_coding(),
                "valueInteger": self.value_counts[code]
            })
        component.append({
            "code": COUNT.as_coding(),
            "valueInteger": total,
        })
        component.append({
            "code": MISSING.as_coding(),
            "valueInteger": self.n - total
        })

        return component


class ComponentQuantityParser(ComponentDataParser):
    def __init__(self, resource):
        super().__init__(resource)

        self.min = 0.0
        self.max = 0.0

        if 'qualifiedInterval' in resource:
            range = resource['qualifiedInterval'].get('range')

            if range is not None:
                if 'low' in range:
                    self.min = range['low']
                if 'high' in range:
                    self.max = range['high']

        self.units = ""
        if 'quantitativeDetails' in resource:
            units = resource['quantitativeDetails'].get('unit')
            if units is not None:
                self.units = GetValue(units, 'code')

        # We'll capture sum and count to produce a mean
        self.sum = 0.0
        self.count = 0

    def ParseData(self, component):
        if 'valueQuantity' in component:
            self.sum += component['valueQuantity']['value']
        elif 'valueString' in component:
            self.note_mismatched(component['valueString'])
        self.count += 1


    def BuildComponents(self):
        component = [{
            "code": COUNT.as_coding(),
            "valueInteger": self.count,
        }, {  
            "code": MEAN.as_coding()  
        }, {
            "code": MISSING.as_coding(),
            "valueInteger": self.n - self.count
        }
        ]

        try:
            component[1]["valueQuantity"] = { "value": self.sum/float(self.count) }
        except:
            component[1]["valueString"] = "NaN"

        return component

    def return_text_results(self):       
        mean = "NaN"
        try:
            mean = self.sum/float(self.count)
        except:
            mean = "NaN"
        return f"""      N: {self.count}\n""" + self.list_mismatched_counts() + \
f"""      mean: {mean}
      missing: {self.n - self.count}\n"""

def SelectKeyCode(coding):
    # For now, just take the first

    # We have another, more pressing issue. Our observation definitions and 
    # component codes don't always match due to the fact that we are sharing
    # the same data-dictionary across all of these common datasets. We need
    # to finalize a solution to this problem for everything to work correctly. 
    return f"{coding['coding'][0]['system'].split('/')[-1]}|{coding['coding'][0]['code']}"

class SourceTable(Summary):
    def __init__(self, activitydef, observationdefs):

        meta_tag = activitydef['meta']['tag'][0]
        self.meta_tag = f"{meta_tag['system']}|{meta_tag['code']}"
        self.table_name = OfficialIdentifier(activitydef['identifier'])['value']
        self.title = GetValue(activitydef, "title")
        self.observation_definitions = {}

        self.n = 0

        odids = set([req['reference'].split("/")[-1] for req in activitydef['observationResultRequirement']])

        for obsdef in observationdefs:
            if obsdef['id'] in odids:
                self.add_od(obsdef)

        print(f"Activity Definition '{self.table_name}' Loaded with {len(self.observation_definitions)} out of {len(odids)}: ")
    
    def add_od(self, resource):
        # Factory to load the appropriate parser/loader object based on the
        # respective permittedDataType value

        permitted_data_types = resource['permittedDataType']

        if 'CodeableConcept' in permitted_data_types:
            parser = ComponentValueSetParser(resource)
        elif 'string' in permitted_data_types:
            parser = ComponentStringParser(resource)
        elif 'Quantity' in permitted_data_types:
            parser = ComponentQuantityParser(resource)
        else:
            print(f"What do we do with these? {','.join(permitted_data_types)}")
            sys.exit(1)

        self.observation_definitions[parser.code] = parser

    def load_source_data(self):
        # Load all of the observations associated with this study and
        # the source data code
        
        client = GetInputClient()
        print(f"Pulling observations for tag: {self.meta_tag}")

        result = client.get(f"Observation?_tag={self.meta_tag}&code={source_data_code}")
        if result.success():
            for entry in result.entries:
                self.ParseData(entry['resource'])
    
    def get_observation_table(self, resource):
        return resource['code']['coding'][1]['code']

    def ParseData(self, resource):
        # Make sure we are looking at the right table
        resource_table = self.get_observation_table(resource)

        if resource_table == self.table_name:
            self.n += 1
            for component in resource['component']:
                coding = component['code']
                try:
                    code = SelectKeyCode(coding)
                except:
                    print(f"There was a problem getting the code from the following")
                    print(coding)
                    pdb.set_trace()

                # If there are more than one table in the dataset, then not all 
                # variables can be expected to be present in this table's row
                if code in self.observation_definitions:
                    self.observation_definitions[code].ParseData(component)
                else:
                    print("\t" + "\n\t".join(sorted(self.observation_definitions.keys())))
                    print(f"{self.table_name} skipping {code}")

                    pdb.set_trace()


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

        for od in sorted(self.observation_definitions.keys()):
            summary = deepcopy(observation_base)

            obsdef = self.observation_definitions[od]
            obsdef.n = self.n

            summary['identifier'] = [obsdef.identifier]
            # Let's inject our population ID into this value just to permit 
            # multiple consent IDs
            summary['identifier'][0]['value'] = f"{population.id}.{summary['identifier'][0]['value']}"
            summary['valueCodeableConcept'] = obsdef.coding
            summary['valueCodeableConcept']['text'] = obsdef.code

            summary['component'] += obsdef.BuildComponents()

            summaries.append(summary)

        return summaries

    def return_text_results(self):        
        result = f"  {self.table_name}:\n"

        for od in sorted(self.observation_definitions.keys()):
            self.observation_definitions[od].n = self.n
            result += f"    {od}:\n"
            result += self.observation_definitions[od].return_text_results()

        return result
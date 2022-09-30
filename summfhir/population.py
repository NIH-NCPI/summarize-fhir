"""
The population associated with a group of research subjects for which summaries
will be produced
"""

from summfhir import GetInputClient, OfficialIdentifier
from summfhir.patient import Patient
from summfhir.condition import Condition
from summfhir.observation_source import SourceTable
from collections import defaultdict 
from re import compile
import sys

class NoTableFound(Exception):
    def __init__(self, identifier):
        super().__init__(self.msg())
        self.identifier = identifier[0]['value']
    
    def msg(self):
        return f"The summary data for '{self.identifier}' has no table code "

class Population:
    regex_data_table = compile("CodeSystem/[\w\-/]*/dataset")
    def __init__(self, resource):
        self.id = resource['id']
        self.tag = resource['meta']['tag'][0]['code']
        self.quantity = resource['quantity']
        self.members = set([x['entity']['reference'] for x in resource['member']])

        self.population_id = OfficialIdentifier(resource['identifier'])

        self.summaries = {}

    def is_member(self, patient_ref):
        return patient_ref in self.members

    # This definitely could use the references in self.members, but if we can
    # take advantage of this feature, then this should be faster
    def summarize_patients(self):
        all_patients = []

        client = GetInputClient()
        result = client.get(f"Patient?_tag={self.tag}")
        if result.success():
            for entry in result.entries:
                patient = entry['resource']
                if self.is_member(f"Patient/{patient['id']}"):
                    all_patients.append(patient)
        
        # At some point, we'll handle no tag options 
        self.summaries['Demographics'] = Patient(all_patients)

    def summarize_conditions(self):
        all_conditions = []

        client = GetInputClient()
        result = client.get(f"Condition?_tag={self.tag}")
        if result.success():
            for entry in result.entries:
                condition = entry['resource']

                if 'subject' in condition:
                    if self.is_member(condition['subject']['reference']):
                        all_conditions.append(condition)
        
        # At some point, we'll handle no tag options 
        self.summaries['Conditions'] = Condition(all_conditions)

    def source_table(self, coding):
        for code in coding:
            if Population.regex_data_table(code['system']):
                return code
        return None

    def summarize_source(self):
        activity_definitions = []
        observation_definitions = []

        client = GetInputClient()
        result = client.get(f"ActivityDefinition?_tag={self.tag}")
        if result.success():
            activity_definitions = [entity['resource'] for entity in result.entries]

        result = client.get(f"ObservationDefinition?_tag={self.tag}")
        if result.success():
            observation_definitions = [entity['resource'] for entity in result.entries]

        if len(activity_definitions) * len(observation_definitions) < 1:
            print(f"{len(activity_definitions)} Activity definitions and "
            "{len(observation_definitions). Unable to proceed with "
            "summarization. ")
            sys.exit(1)

        for ad in activity_definitions:
            table = SourceTable(ad, observation_definitions)
            table.load_source_data()
            self.summaries[table.table_name] = table

    def return_text_results(self):
        results = f""

        for header in self.summaries:
            results += f"{header}: \n" + self.summaries[header].return_text_results()

        return results

    def return_summaries(self):
        summaries = []
        for header in self.summaries:
            summaries += self.summaries[header].BuildSummaryObservations(self)
        return summaries
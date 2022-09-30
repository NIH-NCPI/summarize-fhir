"""
aggregate all of the study details for a single study into one place.
"""

from summfhir import GetInputClient, GetOutputClient, InitMetaTag
from summfhir.population import Population
from pathlib import Path
import json
import pdb
from time import sleep

from pprint import pformat

class StudySummary:
    def __init__(self, resource):
        meta_tag = resource['meta']['tag'][0]
        self.id = resource['id']
        self.tag = meta_tag['code']
        self.title = resource['title']
        self.enrollment = []

        InitMetaTag(meta_tag['system'], meta_tag['code'])

        client = GetInputClient()
        for group in resource['enrollment']:
            result = client.get(group['reference'])
            if result.success():
                self.enrollment.append(Population(result.entries[0]))

    def summarize_patients(self):
        for pop in self.enrollment:
            pop.summarize_patients()
    
    def summarize_conditions(self):
        for pop in self.enrollment:
            pop.summarize_conditions()

    def summarize_source(self):
        for pop in self.enrollment:
            pop.summarize_source()
    
    def build_text_report(self, outdir="output/summaries"):
        dir = Path(outdir)
        dir.mkdir(parents=True, exist_ok=True)

        for population in self.enrollment:
            result_filename = dir / f"{population.population_id['value'].lower()}.yaml"
            with result_filename.open('wt') as outf:
                outf.write(population.return_text_results())

            print(result_filename)

    def load_observations(self, outdir="output/summaries"):
        dest_server = GetOutputClient()

        summaries = []
        for population in self.enrollment:
            local_summaries = population.return_summaries()

            print(f"{population.tag} - {len(local_summaries)} summaries")
            summaries += local_summaries
        dir = Path(outdir)
        dir.mkdir(parents=True, exist_ok=True)
        result_filename = dir / f"{population.population_id['value'].lower()}.json"


        with result_filename.open('wt') as outf:
            json.dump(summaries, outf, indent=2)
        print(result_filename)        

        print("Loading to server: ")
        for summary in summaries:
            try:
                system = summary['identifier'][0]['system']
                value = summary['identifier'][0]['value']
            except:
                print(pformat(summary['identifier']))
                pdb.set_trace()
            identifier_type = "identifier"

            retry_count = 5
            while retry_count > 0:
                retry_count -= 1
                result = dest_server.post('Observation',
                            summary,
                            identifier=value,
                            identifier_system=system,
                            identifier_type=identifier_type)
                if result['status_code'] < 300:
                    retry_count = 0
                elif retry_count < 0:
                    print("\tToo many retries. Giving up on this one. ")
                    pdb.set_trace()
                else:
                    print(pformat(result))
                    print(f"\t{result['status_code']} : {result['request_url']}")
                    sleep(5)
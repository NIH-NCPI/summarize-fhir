"""

Capture the summary as a string of components inside a single Observation

"""

from summfhir import MetaTag, _identifier_prefix

# I'm not entirely sure this is necessary, but if it is, do we want to split
# them up to be conditions, demographics, etc for easy collection of different
# types of summaries? If we filter on demographics, you could get race, 
# ethnicity and gender without having to specify them individually, and yet
# not have to deal with sifting through all of those conditions
NCPI_SUMMARY_CS = {
  "resourceType": "CodeSystem",
  "status": "active",
  "content": "fragment",
  "name": "StudySummaryTypes",
  "id": "study-summary-types",
  "title": "Study Summary Types",
  "description": "Study Summary Types",
  "version": "0.1.0",
  "url": "https://https://nih-ncpi.github.io/ncpi-fhir-ig/fhir/code-systems/summary_types",
  "concept": [
    {
      "code": "variable-summary",
      "display": "Variable Summary"
    },
    {
      "code": "demographics-summary",
      "display": "Demographics Summary"
    },
    {
      "code": "condition-summary",
      "display": "Condition Summary"
    }
  ],
  "experimental": false,
  "publisher": "NCPI FHIR Works"
}


class SummaryOutput:
    # Once we go live with the new IG with summary profiles, we'll update
    # this with the appropriate profile name
    def __init__(self, name, summary_type_code, groupref, varcode, profile=None):
        self.profile = profile
        self.name = name

        # This indicates the subject of the summary (which will be a group)
        self.groupref = groupref

        # Type of summary
        self.code = summary_type_code            

        # For regular DD based variables, this is from the DD Code System
        # for conditions, this will be the HPO Code or whatever. For true
        # demographic summaries (from the patient resources) we'll have  codes
        # here as well, but they will be something from a public system
        self.varcode = varcode      
        self.components = []

    def add_component(self, component):
        self.components.append(component)
        
    def objectify(self):
        entity = {
            "resourceType": "Observation",
            "meta": {
                "tag": MetaTag()
            },
            "identifier": [{
                "system": f"{_identifier_prefix}/observation/summary",
                "value": self.name
            }],
            "status": "final",
            "subject": self.groupref,
            "code": {
                "coding": [
                    self.code
                ],
                "text": self.code['display']
            },
            "valueCodeableConcept": self.varcode,
            "component": self.components
        }

        if self.profile is not None:
            entity['meta']['profile'] = self.profile


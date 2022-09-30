__version__="0.0.1"

import sys

_fhir_input = None
_fhir_output = None

# This is the prefix associated with the study whose data we are summarizing. 
# We may be able to acquire this using some data 
_identifier_prefix = None

_tag_system = None
_tag_code = None

def InitMetaTag(system, code):
    global _tag_system, _tag_code

    _tag_system = system
    _tag_code = code

def MetaTag():
    if _tag_system is None or _tag_code is None:
        sys.stderr.write("Application must define tag code and it's system to proceed")
        sys.exit(1)

    return [{
            "system": _tag_system,
            "code": _tag_code
    }]


class InvalidClient(Exception):
    def __init__(self, client_mode="Input"):
        self.mode = client_mode

        super().__init__(self.message())
    
    def message(self):
        return f"The {self.mode} FHIR client is invalid. Unable to proceed."

class Coding:
    def __init__(self, code=None, display=None, system=None, resource=None):
        if resource is not None:
            self.system = resource.get("system")
            self.version = resource.get("version")
            self.code = resource.get("code")
            self._display = resource.get("display")

        if code is not None:
            self.code = code
        
        if display is not None:
            self._display = display

        if system is not None:
            self.system = system

    def as_code(self):
        return {
                "code": self.code,
                "display": self.display,
                "system": self.system
            }

    def as_coding(self):
        return {
            "coding": [self.as_code()]
        }

    @property
    def display(self):
        if self._display is None:
            return self.code
        return self._display

def BuildCoding(code, display, system):
    return Coding(code=code, display=display, system=system)

def SetInputClient(fhir_client):
    global _fhir_input, _fhir_output
    _fhir_input = fhir_client

    # By default, we use the same in and out server
    # however the application can set the output to 
    # a different server if the user wishes
    if _fhir_output is None:
        _fhir_output = fhir_client

def SetOutputClient(fhir_client):
    _fhir_output = fhir_client

def GetInputClient():
    if _fhir_input is None:
        raise InvalidClient()

    return _fhir_input

def GetOutputClient():
    if _fhir_output is None:
        raise InvalidClient("Output")
    
    return _fhir_output

# Return "" if the key isn't present in the resource
def GetValue(resource, key):
    val = resource.get(key)
    if val is None:
        val = ""
    return val

def AddCoding(code, display, system):
    return {
        "code": code,
        "display": display,
        "system": system
    }

def OfficialIdentifier(identifiers):
    # Capture the first in case there isn't one marked as 'Official'
    official_identifier = identifiers[0]

    for identifier in identifiers:
        if "use" in identifier and identifier['use'] == "official":
            official_identifier = identifier
    
    return official_identifier
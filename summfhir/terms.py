
from summfhir import Coding, BuildCoding



NCIT = "https://uts.nlm.nih.gov/uts/umls"
LOINC = "https://loinc.org"
UCUM = "https://unitsofmeasure.org"

COUNT = BuildCoding('C0750480', "Count", NCIT)
DISTINCT = BuildCoding('C3641802', "Distinct Product Count", NCIT)
SUM = BuildCoding("C25697", "Sum", NCIT)
MEAN = BuildCoding("C0444504", "Statistical Mean", NCIT)
RANGE = BuildCoding("C2348147", "Sample Range", NCIT)
SUMMARY_REPORT = BuildCoding("C0242482", "Summary Report", NCIT)
GENDER = BuildCoding("C0079399", "Gender", NCIT)
MISSING = BuildCoding("C142610", "Missing Data", NCIT)
ETHNICITY = BuildCoding("69490-1", "Ethnicity OMB.1997", "https://loinc.org")
RACE = BuildCoding("32624-9", "Race", "https://loinc.org")
SEX = BuildCoding("46098-0", "sex", "https://loinc.org")

VAR_SUM_CC = {
    "coding": [SUMMARY_REPORT.as_code()],
    "text": "Variable Summary Report"
}

TABLE_SUM_CC = {
    "coding": [SUMMARY_REPORT.as_code()],
    "text": "Table Summary Report"
}
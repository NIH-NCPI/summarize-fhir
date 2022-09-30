# summarize-fhir
Summarize FHIR datasets that conform to the NCPI FHIR IG (with data-dictionary module)

This application will summarize Patients and Conditions, building out Observations for each variable such as Race, Ethnicity, Gender as well as each of the distinct sets of HP/Mondo/Maxo codes found. Each observation contains counts for any categorical (valueCodeableConcept) or mean/missing for numeric type variables. 

If there is raw-data and data-dictionary components that conform to the in-development model for those items in FHIR, those too can be summarized. 

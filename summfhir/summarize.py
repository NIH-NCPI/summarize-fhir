"""

Cheats to be used: 
* We'll use the meta tag to filter out all but resources tied directly to the 
study of interest

* 

Based on our model:

Each study has one or more groups referenced by ResearchStudy.enrollment
    for each of these, load the references for the patients 

    Pass the references to the appropriate Summary factory (Patient, condition,
    variable). These references will be used to ignore irrelevant data without
    having run many, many queries
    
"""

import sys
from argparse import ArgumentParser, FileType

import json
from ncpi_fhir_client.fhir_client import FhirClient
from yaml import safe_load
from summfhir import SetInputClient
from summfhir.study import StudySummary

# This should probably get moved over to fhir_client so that this tool doesn't 
# require whistler, since this really isn't specific to Whistler...only the 
# model we are using in whistler
from wstlr import get_host_config

def BuildStudySummaries(study_tag, 
                    fhirclient, 
                    summarize_patients, 
                    summarize_conditions, 
                    summarize_source):
    
    result = fhirclient.get(f"ResearchStudy?_tag={study_tag}")
    if result.success():
        for entry in result.entries:
            study = StudySummary(entry['resource'])
            if summarize_patients:
                study.summarize_patients()
            if summarize_conditions:
                study.summarize_conditions()
            if summarize_source:
                study.summarize_source()

    return study

def exec(args=None):
    if args is None:
        args = sys.argv[1:]

    host_config = get_host_config()
    # Just capture the available environments to let the user
    # make the selection at runtime
    env_options = sorted(host_config.keys())

    parser = ArgumentParser(description="Generate FHIR summary results for"
                    "the specified FHIR ResearchStudy",
                            epilog="By default, all summaries are active, "
                    "however if any of the flags, condition, patient or "
                    "source are active, only the summaries specified are "
                    "performed.")
    parser.add_argument(
        "--host",
        choices=env_options,
        default=None,
        help=f"Remote configuration to be used to access the FHIR server. If "
            "no environment is provided, the system will stop after "
            "generating the whistle output (no validation, no loading)",
    )
    parser.add_argument(
        "-e", 
        "--env", 
        choices=["local", "dev", "qa", "prod"],
        help=f"If your config has host details configured, you can use these "
            "short cuts to choose the appropriate host details. This is useful "
            "if you wish to run different configurations on the same command, "
            "but each has a different target host. Using this requires a "
            "config file. "
    )
    parser.add_argument(
        "config",
        nargs='*',
        type=FileType('rt'),
        help="Dataset YAML file with details required to run conversion. This "
            "isn't required if a study id is provided",
    )
    parser.add_argument(
        "-t",
        "--meta-tag",
        type=str,
        default="",
        help="Short ID code associated with study captured in the meta "
            "property of each resource"
    )
    parser.add_argument(
        "-p", 
        "--patient",
        action='store_true',
        help="Summarize demographics"
    )
    parser.add_argument(
        "-c", 
        "--condition",
        action='store_true',
        help="Summarize conditions"
    )
    parser.add_argument(
        "-s", 
        "--source",
        action='store_true',
        help="Summarize source tables"
    )

 
    args = parser.parse_args(sys.argv[1:])

    host = args.host
    tag = args.meta_tag

    summarize_all = not (args.patient and args.condition and args.source)
    summarize_patients = summarize_all or args.patient
    summarize_conditions = summarize_all or args.condition
    summarize_source = summarize_all or args.source



    for config_file in args.config:
        config = safe_load(config_file)

        environment = config.get("env")

        if args.env is None and host is None:
            args.env = 'local'
            print("Defaulting to the local environment")

        if args.env is not None:
            if args.env not in environment:
                print(f"The environment, {args.env}, is not configured in {config}.")
                sys.exit(1)

            if args.host is not None:
                print(f"Specifying both a host and and environment doesn't make sense. Please use only --env or --host")
                sys.exit(1)

            host = environment[args.env]

            if "study_id" in config and tag == "":
                tag = config["study_id"]
        fhirclient = FhirClient(host_config[host])
        SetInputClient(fhirclient)

        study = BuildStudySummaries(tag, fhirclient, summarize_patients, summarize_conditions, summarize_source)

        study.build_text_report()
        study.load_observations()

import os
from setuptools import setup, find_packages, find_namespace_packages

from summfhir import __version__

root_dir = os.path.dirname(os.path.abspath(__file__))
req_file = os.path.join(root_dir, "requirements.txt")
with open(req_file) as f:
    requirements = f.read().splitlines()

setup(
    name="Summarize-FHIR",
    version=__version__,
    description=f"NCPI Summarize FHIR {__version__}",
    packages=find_namespace_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'summarize = summfhir.summarize:exec'
        ]
    }
)

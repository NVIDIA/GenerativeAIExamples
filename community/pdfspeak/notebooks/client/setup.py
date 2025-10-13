# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0


import datetime
import os
import re

from setuptools import find_packages
from setuptools import setup


def get_version():
    release_type = os.getenv("NV_INGEST_RELEASE_TYPE", "dev")
    version = os.getenv("NV_INGEST_CLIENT_VERSION")
    rev = os.getenv("NV_INGEST_REV", "0")

    if not version:
        version = f"{datetime.datetime.now().strftime('%Y.%m.%d')}"

    # Ensure the version is PEP 440 compatible
    pep440_regex = r"^\d{4}\.\d{1,2}\.\d{1,2}$"
    if not re.match(pep440_regex, version):
        raise ValueError(f"Version '{version}' is not PEP 440 compatible")

    # Construct the final version string
    if release_type == "dev":
        final_version = f"{version}.dev{rev}"
    elif release_type == "release":
        final_version = f"{version}.post{rev}" if int(rev) > 0 else version
    else:
        raise ValueError(f"Invalid release type: {release_type}")

    return final_version


def read_requirements(file_name):
    """Read a requirements file and return a list of its packages."""
    with open(file_name) as f:
        return f.read().splitlines()


# Specify your requirements files
base_dir = os.path.abspath(os.path.dirname(__file__))
requirements_files = []

# Read and combine requirements from all specified files
combined_requirements = []
for file in requirements_files:
    combined_requirements.extend(read_requirements(file))

combined_requirements = list(set(combined_requirements))

setup(
    author="Anuradha Karuppiah",
    author_email="anuradhak@nvidia.com",
    classifiers=[],
    description="Python client for the nv-ingest service",
    entry_points={
        "console_scripts": [
            "nv-ingest-cli=nv_ingest_client.nv_ingest_cli:main",
            "process-json-files=nv_ingest_client.util.process_json_files:main",
        ]
    },
    install_requires=combined_requirements,
    name="nv_ingest_client",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    version=get_version(),
    license="Apache-2.0",
)

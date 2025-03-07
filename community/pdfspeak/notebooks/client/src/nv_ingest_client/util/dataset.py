# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import os
import random
from collections import Counter
from io import BytesIO
from io import StringIO
from pprint import pformat


def get_dataset_statistics(dataset_bytes: BytesIO) -> str:
    """
    Reads a dataset specification from a BytesIO object, computes statistics about the dataset,
    and returns a formatted string.

    Parameters
    ----------
    dataset_bytes : BytesIO
        The BytesIO object containing the dataset in JSON format.

    Returns
    -------
    str
        A formatted string containing statistics about the dataset.
    """
    try:
        dataset_bytes.seek(0)
        dataset = json.load(dataset_bytes)
    except json.JSONDecodeError:
        raise

    sampled_files = dataset.get("sampled_files", [])
    metadata = dataset.get("metadata", {})

    # Compute statistics
    file_types = [os.path.splitext(file)[1][1:].lower() for file in sampled_files]
    file_type_counts = Counter(file_types)
    unique_files = set(sampled_files)
    unique_file_types = {
        file_type: len(set(f for f in sampled_files if f.endswith("." + file_type))) for file_type in file_type_counts
    }

    total_size_bytes = sum(os.path.getsize(f) for f in sampled_files)
    total_size_gb = total_size_bytes / (1024**3)

    file_type_sizes = {
        ftype: sum(os.path.getsize(f) for f in sampled_files if f.endswith("." + ftype)) for ftype in file_type_counts
    }
    file_type_sizes_gb = {ftype: size / (1024**3) for ftype, size in file_type_sizes.items()}

    estimated_sizes_gb = {
        ftype: metadata["file_type_proportions"][ftype]["target_proportion"] / 100 * total_size_gb
        for ftype in metadata["file_type_proportions"]
    }

    # Format statistics as a string
    stats_stringio = StringIO()
    stats = {
        "metadata": metadata,
        "total_number_of_files": len(sampled_files),
        "total_number_of_unique_files": len(unique_files),
        "total_number_of_files_per_file_type": file_type_counts,
        "total_number_of_unique_files_per_file_type": unique_file_types,
        "total_size_gb": total_size_gb,
        "total_size_per_file_type_gb": file_type_sizes_gb,
        "estimated_total_size_per_file_type_gb": estimated_sizes_gb,
    }
    stats_stringio.write("Dataset Statistics:\n")
    stats_stringio.write(pformat(stats))

    return stats_stringio.getvalue()


def get_dataset_files(dataset_bytes: BytesIO, shuffle: bool = False) -> list:
    """
    Extracts and optionally shuffles the list of files contained in a dataset.

    Parameters
    ----------
    dataset_bytes : BytesIO
        The BytesIO object containing the dataset in JSON format.
    shuffle : bool, optional
        Whether to shuffle the list of files before returning. Defaults to False.

    Returns
    -------
    list
        The list of files from the dataset, possibly shuffled.
    """
    try:
        dataset_bytes.seek(0)
        dataset = json.load(dataset_bytes)
        sampled_files = dataset.get("sampled_files", [])
        if shuffle:
            random.shuffle(sampled_files)
        return sampled_files
    except json.JSONDecodeError as err:
        raise ValueError(f"{err}")

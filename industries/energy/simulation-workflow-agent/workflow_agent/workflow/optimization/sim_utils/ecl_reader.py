# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import struct
import os
import logging
import glob
from datetime import datetime

# Module-level logger
logger = logging.getLogger(__name__)


class EclReader:
    """Reads SLB ECLIPSE style binary output files (.INIT, .EGRID, .UNRST, .X00xx).

    This class provides methods to read various ECLIPSE output files, including
    initial conditions (.INIT), grid data (.EGRID), and restart files (.UNRST, .X00xx).
    It handles endianness detection and data type conversion.

    Attributes:
        input_file_path (str): Path to the main ECLIPSE input file (.DATA or .IXF).
        input_file_path_base (str): Base path of the input file (without extension).
        init_file_path (str): Path to the initial conditions file (.INIT).
        egrid_file_path (str): Path to the grid data file (.EGRID).
        unrst_file_path (str): Path to the unified restart file (.UNRST).  Currently not used.
    """

    def __init__(self, input_file_path: str) -> None:
        """Initializes the EclReader object.

        Parameters
            input_file_path (str): Path to the main ECLIPSE input file (.DATA or .AFI).

        Raises:
            FileNotFoundError: If the input file or any required related file is not found.
            RuntimeError: If the input file has an unsupported extension.
        """
        self.input_file_path = input_file_path
        self._validate_input_file()
        self._initialize_file_names()

    def read_init(self, keys: list = None) -> dict:
        """Reads data from the initial conditions file (.INIT).

        Parameters
            keys (list, optional): List of keys to read. If None, all keys are read. Defaults to None.

        Returns
            dict: Dictionary containing the requested data, keyed by the provided keys.
                Returns an empty dictionary if no keys are provided.
        """
        return self._read_bin(self.init_file_path, keys)

    def read_egrid(self, keys: list = None) -> dict:
        """Reads data from the grid data file (.EGRID).

        Parameters
            keys (list, optional): List of keys to read. If None, all keys are read. Defaults to None.

        Returns
            dict: Dictionary containing the requested data, keyed by the provided keys.
                Returns an empty dictionary if no keys are provided.
        """
        return self._read_bin(self.egrid_file_path, keys)

    def read_restart(self, keys: list = None, tstep_id: int = None) -> dict:
        """Reads restart data from .UNRST or .X00xx files (automatically selected).

        Parameters
            keys (list): List of variables to extract.
            tstep_id (int, optional): Specific timestep. If None, reads all available.

        Returns
            dict: { timestep_id: { "DATE": ..., "TIME": ..., key1: ..., ... }, ... }

        Raises:
            FileNotFoundError: If no restart files found.
        """

        # Try unified first
        unified_file = f"{self.input_file_path_base}.UNRST"
        if os.path.exists(unified_file):
            return self._read_unrst(unified_file, keys, tstep_id)

        # Else fallback to .X00xx
        base_dir = os.path.dirname(self.input_file_path_base)
        base_name = os.path.basename(self.input_file_path_base)
        search_pattern = os.path.join(base_dir, f"{base_name}.X[0-9][0-9][0-9][0-9]")
        files = sorted(glob.glob(search_pattern))

        if not files:
            raise FileNotFoundError("No restart files (.UNRST or .X00xx) were found.")

        # Single-step case (still wrap output in dict)
        if tstep_id is not None:
            match_file = f"{self.input_file_path_base}.X{self._int2ext(tstep_id)}"
            if not os.path.exists(match_file):
                raise FileNotFoundError(f"Restart file not found: {match_file}")

            data = self._read_bin(match_file, keys)
            result = self._add_date_and_time(data)
            return {tstep_id: result}

        # Multi-step case: read all .X00xx files
        all_results = {}
        previous_date = None
        cumulative_days = 0

        for fpath in files:
            tstep = int(os.path.basename(fpath).split("X")[-1])
            try:
                data = self._read_bin(fpath, keys)
            except Exception as e:
                logging.warning(f"Skipping {fpath} due to error: {e}")
                continue

            result = self._add_date_and_time(data, previous_date, cumulative_days)
            if "DATE" in result:
                current_date = result["DATE"]
                cumulative_days = result["TIME"]
                previous_date = current_date

            all_results[tstep] = result

        return all_results

    def read_smry(self, keys: list, entities: list = None) -> dict:
        """Reads summary data from .UNSMRY or .Sxxxx files for fields, wells, or groups.

        Parameters
            keys (list): Summary variable names to extract (e.g., ["WBHP", "WOPR"]).
            entities (list, optional): List of entities (e.g., wells or groups like ["INJ", "PROD", "FIELD"]).
                                       If None, all unique entities will be used.

        Returns
            dict: {
                "TIME": np.ndarray,
                "<ENTITY_1>": { "<KEY_1>": np.ndarray, ... },
                ...
            }

        Raises:
            FileNotFoundError: If the .SMSPEC or summary output files are missing.
        """
        smspec_file = f"{self.input_file_path_base}.SMSPEC"
        if not os.path.exists(smspec_file):
            raise FileNotFoundError(
                f"Summary specification file not found: {smspec_file}"
            )

        # --- Step 1: Read key/entity info from SMSPEC using pattern matching ---
        with open(smspec_file, "rb") as fid:
            file_data = fid.read()

        # Detect endian from the first 4 bytes
        first_int = struct.unpack("<i", file_data[:4])[0]
        if first_int > 0 and first_int < 1000:  # Reasonable header size
            endian = "<"
        else:
            endian = ">"

        # Find KEYWORDS and WGNAMES/NAMES positions by pattern matching
        keywords_pos = file_data.find(b"KEYWORDS")
        wgnames_pos = file_data.find(b"WGNAMES")
        names_pos = file_data.find(b"NAMES")

        if keywords_pos == -1:
            raise ValueError("KEYWORDS record not found in SMSPEC file")

        # Read KEYWORDS data
        keywords_pos -= 4  # Go back to record start
        with open(smspec_file, "rb") as fid:
            fid.seek(keywords_pos)
            raw_keys, n_key = self._read_smspec_record(fid, endian)

        # Read entity names (try WGNAMES first, then NAMES)
        if wgnames_pos != -1:
            entity_pos = wgnames_pos - 4
        elif names_pos != -1:
            entity_pos = names_pos - 4
        else:
            raise ValueError("Neither WGNAMES nor NAMES record found in SMSPEC file")

        with open(smspec_file, "rb") as fid:
            fid.seek(entity_pos)
            raw_entities, n_ent = self._read_smspec_record(fid, endian)

        if n_key != n_ent:
            raise ValueError(
                f"Mismatch between number of keys ({n_key}) and entities ({n_ent}) in .SMSPEC."
            )

        all_keys = ["".join(row).strip() for row in raw_keys]
        all_entities = ["".join(row).strip() for row in raw_entities]

        if entities is None:
            entities = sorted(set(all_entities))
            # entities = ["FIELD" if s == ':+:+:+:+' else s for s in entities]

        n_keys = len(keys)
        n_ents = len(entities)

        # Build lookup table (flat index map)
        index_map = {
            (k, e): i
            for i, (k, e) in enumerate(zip(all_keys, all_entities))
            if k in keys and e in entities
        }

        # --- Step 2: Read UNSMRY or Sxxxx files ---
        time_series = []
        summary_data = []

        files = [f"{self.input_file_path_base}.UNSMRY"]
        if not os.path.exists(files[0]):
            base_dir = os.path.dirname(self.input_file_path_base)
            base_name = os.path.basename(self.input_file_path_base)
            pattern = os.path.join(base_dir, f"{base_name}.S[0-9][0-9][0-9][0-9]")
            files = sorted(glob.glob(pattern))

        for fname in files:
            if not os.path.exists(fname):
                logging.warning(f"Skipping missing summary file: {fname}")
                continue

            with open(fname, "rb") as fid:
                self._load_vector(fid, endian)  # Skip SEQHDR

                while True:
                    _, _, label = self._load_vector(fid, endian)  # MINISTEP or SEQHDR
                    if label == "SEQHDR":
                        continue

                    data, _, _ = self._load_vector(fid, endian)
                    if data is None or len(data) == 0:
                        break

                    time_series.append(data[0])

                    row = np.full((n_keys, n_ents), np.nan, dtype=np.float32)
                    for i, key in enumerate(keys):
                        for j, ent in enumerate(entities):
                            idx = index_map.get((key, ent), -1)
                            if idx >= 0:
                                row[i, j] = data[idx]
                    summary_data.append(row)

        # --- Step 3: Restructure output ---
        time_series = np.array(time_series)
        summary_data = np.array(summary_data)  # [timesteps, n_keys, n_ents]

        result = {"TIME": time_series}
        for j, ent in enumerate(entities):
            ent_block = {
                keys[i]: summary_data[:, i, j]
                for i in range(n_keys)
                if not np.all(np.isnan(summary_data[:, i, j]))
            }
            if ent_block:
                if ent == ":+:+:+:+":
                    ent = "FIELD"
                result[ent] = ent_block

        return result

    # ---- Private Methods ---------------------------------------------------------------------------------------------

    def _validate_input_file(self) -> None:
        """Validates the input file and its extension.

        Raises:
            FileNotFoundError: If the input file is not found.
            RuntimeError: If the input file has an unsupported extension.
        """
        if not os.path.exists(self.input_file_path):
            raise FileNotFoundError(f"Input file not found: {self.input_file_path}")

        base, ext = os.path.splitext(self.input_file_path)
        if ext.upper() not in [".DATA", ".AFI"]:
            raise RuntimeError(f"Unsupported input file: {self.input_file_path}")

        self.input_file_path_base = base

    def _initialize_file_names(self) -> None:
        """Initializes file paths for related binary files (.INIT, .EGRID, .UNRST)."""
        self.init_file_path = f"{self.input_file_path_base}.INIT"
        self.egrid_file_path = f"{self.input_file_path_base}.EGRID"
        self.unrst_file_path = f"{self.input_file_path_base}.UNRST"

    def _read_bin(self, file_path: str, keys: list) -> dict:
        """Reads ECLIPSE style binary data from the given file.

        Parameters
            file_path (str): Path to the binary file.
            keys (list): List of keys to read.

        Returns
            dict: Dictionary containing the requested data. Returns an empty dictionary if keys is None.
        """

        if keys is None:
            logging.warning("No keys provided.")
            return {}

        logging.debug(f"Reading keys: {keys} in file: {file_path}")

        variables = {}
        with open(file_path, "rb") as fid:
            endian = self._detect_endian(fid)
            found_keys = {key: False for key in keys}

            while keys and not all(found_keys.values()):
                data, _, key = self._load_vector(fid, endian)
                key = key.strip()
                if key in found_keys:
                    # Dynamically determine dtype
                    if isinstance(data, np.ndarray):
                        variables[key] = data  # Keep original dtype
                    elif isinstance(data, (bytes, str)):
                        variables[key] = data.decode(
                            errors="ignore"
                        ).strip()  # Convert bytes to string
                    elif isinstance(data, (int, float)):
                        variables[key] = np.array(
                            [data], dtype=np.float32
                        )  # Convert scalars to array
                    else:
                        logging.warning(f"Unknown data type for key: {key}")
                        variables[key] = data  # Store as-is

                    found_keys[key] = True

                if fid.tell() >= os.fstat(fid.fileno()).st_size:
                    break

            # Log missing keys (Debug level)
            missing_keys = [k for k, v in found_keys.items() if not v]
            if missing_keys:
                logging.debug(f"The following keys were not found: {missing_keys}")
                for key in missing_keys:
                    variables[key] = np.array([])

        return variables

    def _load_vector(self, fid, endian):
        """Reads a data block (vector) from the binary file.

        Parameters
            fid: File object.
            endian (str): Endianness ('<' for little-endian, '>' for big-endian).

        Returns
            tuple: A tuple containing the data (NumPy array or string), the data count, and the key.
                Returns (None, None, key) if an error occurs during reading.
        """
        try:
            # Read and verify the header
            header_size = struct.unpack(endian + "i", fid.read(4))[0]
            key = fid.read(8).decode(errors="ignore").strip()
            data_count = struct.unpack(endian + "i", fid.read(4))[0]
            data_type_raw = fid.read(4)
            data_type = data_type_raw.decode(errors="ignore").strip().upper()
            end_size = struct.unpack(endian + "i", fid.read(4))[0]

            if header_size != end_size:
                logging.warning(
                    f"Mismatch Detected for {key}: Header={header_size}, End={end_size}"
                )
                return None, None, key  # Skip this entry

            # Define data type mapping
            dtype_map = {
                "CHAR": "S1",
                "INTE": "i4",
                "REAL": "f4",
                "DOUB": "f8",
                "LOGI": "i4",
            }
            dtype = dtype_map.get(data_type)

            if dtype:
                raw_data = bytearray()
                read_count = 0

                while read_count < data_count:
                    # Read the header size of this chunk
                    chunk_size = struct.unpack(endian + "i", fid.read(4))[0]
                    chunk_data = fid.read(chunk_size)
                    chunk_end = struct.unpack(endian + "i", fid.read(4))[0]

                    if chunk_size != chunk_end:
                        logging.warning(
                            f"Chunk mismatch in {key}: Expected {chunk_size}, got {chunk_end}"
                        )
                        return None, None, key

                    raw_data.extend(chunk_data)
                    read_count += chunk_size // np.dtype(dtype).itemsize

                if data_type == "CHAR":
                    char_array = np.frombuffer(raw_data, dtype="S1").reshape(
                        (-1, 8)
                    )  # 8-char wide strings
                    char_array = np.char.decode(char_array, encoding="utf-8").astype(
                        str
                    )
                    return char_array, data_count, key
                else:
                    data = np.frombuffer(raw_data, dtype=endian + dtype)
                    return data, data_count, key
            else:
                fid.seek(data_count * 4, os.SEEK_CUR)  # Skip unknown type
                return None, None, key
        except struct.error:
            return None, None, ""

    def _read_smspec_record(self, fid, endian):
        """Read a single SMSPEC record using pattern matching approach.

        Parameters
            fid: File object positioned at the start of a record
            endian: Endianness string

        Returns
            tuple: (data_array, count)
        """
        try:
            # Read record header
            header_size = struct.unpack(endian + "i", fid.read(4))[0]
            key = fid.read(8).decode("ascii", errors="ignore").strip()
            data_count = struct.unpack(endian + "i", fid.read(4))[0]
            data_type = fid.read(4).decode("ascii", errors="ignore").strip()
            end_size = struct.unpack(endian + "i", fid.read(4))[0]

            if header_size != end_size:
                raise ValueError(
                    f"Header size mismatch for {key}: {header_size} != {end_size}"
                )

            if data_count <= 0:
                return np.array([]), 0

            # Determine bytes per element based on data type
            if data_type == "CHAR":
                bytes_per_element = 8
            else:
                dtype_map = {"INTE": "i4", "REAL": "f4", "DOUB": "f8", "LOGI": "i4"}
                dtype = dtype_map.get(data_type, "i4")
                bytes_per_element = np.dtype(dtype).itemsize

            # Read the data in chunks
            raw_data = bytearray()
            bytes_read = 0
            total_bytes_needed = data_count * bytes_per_element

            while bytes_read < total_bytes_needed:
                chunk_size = struct.unpack(endian + "i", fid.read(4))[0]
                chunk_data = fid.read(chunk_size)
                chunk_end = struct.unpack(endian + "i", fid.read(4))[0]

                if chunk_size != chunk_end:
                    raise ValueError(
                        f"Chunk size mismatch: {chunk_size} != {chunk_end}"
                    )

                raw_data.extend(chunk_data)
                bytes_read += chunk_size

            # Parse the data based on type
            if data_type == "CHAR":
                # For CHAR data, reshape into 8-character strings
                if len(raw_data) >= total_bytes_needed:
                    char_data = np.frombuffer(raw_data, dtype="S1").reshape((-1, 8))
                    char_data = np.char.decode(char_data, encoding="ascii").astype(str)
                    return char_data, data_count
                else:
                    raise ValueError(
                        f"Insufficient CHAR data: expected {total_bytes_needed}, got {len(raw_data)}"
                    )
            else:
                # For numeric data
                if len(raw_data) >= total_bytes_needed:
                    data = np.frombuffer(raw_data, dtype=endian + dtype)
                    return data, data_count
                else:
                    raise ValueError(
                        f"Insufficient {data_type} data: expected {total_bytes_needed}, got {len(raw_data)}"
                    )

        except Exception as e:
            raise RuntimeError(f"Error reading SMSPEC record: {e}")

    def _detect_endian(self, fid):
        """Detects file endianness.

        Parameters
            fid: File object.

        Returns
            str: Endianness ('<' for little-endian, '>' for big-endian).
        """
        fid.seek(0)
        test_int = fid.read(4)
        little_endian = struct.unpack("<i", test_int)[0]
        big_endian = struct.unpack(">i", test_int)[0]
        fid.seek(0)
        return "<" if abs(little_endian) < abs(big_endian) else ">"

    def _int2ext(self, i):
        """Converts an integer to a formatted string with leading zeros (e.g., 1 to "0001").

        Parameters
            i (int): Integer to convert.

        Returns
            str: Formatted string with leading zeros.
        """
        return f"{i:04d}"

    def _read_unrst(
        self, file_path: str, keys: list = None, tstep_id: int = None
    ) -> dict:
        """Read restart data from UNRST file with improved pattern matching."""

        if keys is None:
            keys = []

        all_results = {}
        file_size = os.path.getsize(file_path)

        # Read the entire file into memory for pattern matching
        with open(file_path, "rb") as fid:
            file_data = fid.read()

        # Detect endian from the first 4 bytes
        first_int = struct.unpack("<i", file_data[:4])[0]
        if first_int > 0 and first_int < 1000:  # Reasonable header size
            endian = "<"
        else:
            endian = ">"

        # Find all INTEHEAD positions by pattern matching
        intehead_positions = []
        pos = 0
        while True:
            pos = file_data.find(b"INTEHEAD", pos)
            if pos == -1:
                break
            intehead_positions.append(pos - 4)  # Go back 4 bytes to get to record start
            pos += 8

        # Find all requested key positions by pattern matching
        key_positions = {key: [] for key in keys} if keys else {}
        for key in keys:
            pos = 0
            while True:
                pos = file_data.find(key.encode("ascii"), pos)
                if pos == -1:
                    break

                # Verify this is actually a record header by checking the structure
                if pos >= 4:
                    try:
                        header_size = struct.unpack(
                            endian + "i", file_data[pos - 4 : pos]
                        )[0]
                        if 8 <= header_size <= 1000:  # Reasonable header size range
                            key_positions[key].append(pos - 4)
                    except (struct.error, IndexError):
                        pass  # Skip if we can't unpack

                pos += len(key)

        # Read data from discovered positions
        with open(file_path, "rb") as fid:
            dates = []
            times = []

            # Read INTEHEAD data to get dates
            for intehead_pos in intehead_positions:
                fid.seek(intehead_pos)
                try:
                    header_size = struct.unpack(endian + "i", fid.read(4))[0]
                    key = fid.read(8).decode("ascii", errors="ignore").strip()
                    data_count = struct.unpack(endian + "i", fid.read(4))[0]
                    data_type = fid.read(4).decode("ascii", errors="ignore").strip()
                    end_size = struct.unpack(endian + "i", fid.read(4))[0]

                    if key == "INTEHEAD" and header_size == end_size:
                        # Read the INTEHEAD data to get the date
                        raw_data = bytearray()
                        read_count = 0
                        while read_count < data_count:
                            chunk_size = struct.unpack(endian + "i", fid.read(4))[0]
                            chunk_data = fid.read(chunk_size)
                            chunk_end = struct.unpack(endian + "i", fid.read(4))[0]
                            if chunk_size != chunk_end:
                                break
                            raw_data.extend(chunk_data)
                            read_count += chunk_size // 4

                        if len(raw_data) >= data_count * 4:
                            data = np.frombuffer(raw_data, dtype=endian + "i4")
                            if len(data) > 66:
                                IDAY, IMON, IYEAR = data[64], data[65], data[66]
                                date = datetime(IYEAR, IMON, IDAY)
                                dates.append(date)
                            else:
                                raise ValueError(
                                    f"INTEHEAD data too short: expected >66 elements, got {len(data)}"
                                )
                        else:
                            raise ValueError(
                                f"Failed to read INTEHEAD data: expected {data_count * 4} bytes, got {len(raw_data)}"
                            )
                    else:
                        raise ValueError(
                            f"Invalid INTEHEAD record: key='{key}', header_size={header_size}, end_size={end_size}"
                        )
                except Exception as e:
                    raise RuntimeError(
                        f"Error reading INTEHEAD at position {intehead_pos}: {e}"
                    )

            # Calculate cumulative time from dates
            times = []
            if len(dates) > 0:
                base_date = dates[0]  # Use first date as reference
                for date in dates:
                    time_delta = date - base_date
                    cumulative_days = time_delta.total_seconds() / (
                        24 * 3600
                    )  # Convert to days
                    times.append(cumulative_days)

            # Read data for each timestep
            for timestep_idx, (intehead_pos, date, time) in enumerate(
                zip(intehead_positions, dates, times)
            ):
                result = {"DATE": date, "TIME": time}

                # Read INTEHEAD data for this timestep
                fid.seek(intehead_pos)
                try:
                    header_size = struct.unpack(endian + "i", fid.read(4))[0]
                    key = fid.read(8).decode("ascii", errors="ignore").strip()
                    data_count = struct.unpack(endian + "i", fid.read(4))[0]
                    data_type = fid.read(4).decode("ascii", errors="ignore").strip()
                    end_size = struct.unpack(endian + "i", fid.read(4))[0]

                    if key == "INTEHEAD" and header_size == end_size:
                        # Read the INTEHEAD data
                        raw_data = bytearray()
                        read_count = 0
                        while read_count < data_count:
                            chunk_size = struct.unpack(endian + "i", fid.read(4))[0]
                            chunk_data = fid.read(chunk_size)
                            chunk_end = struct.unpack(endian + "i", fid.read(4))[0]
                            if chunk_size != chunk_end:
                                break
                            raw_data.extend(chunk_data)
                            read_count += chunk_size // 4

                        if len(raw_data) >= data_count * 4:
                            intehead_data = np.frombuffer(raw_data, dtype=endian + "i4")
                            result["INTEHEAD"] = intehead_data
                        else:
                            result["INTEHEAD"] = np.array([])
                    else:
                        result["INTEHEAD"] = np.array([])
                except Exception as e:
                    logging.error(
                        f"Error reading INTEHEAD for timestep {timestep_idx}: {e}"
                    )
                    result["INTEHEAD"] = np.array([])

                # Read requested keys for this timestep
                for key in keys:
                    if key == "INTEHEAD":
                        continue  # Already handled above

                    # Find the key position that comes after this INTEHEAD position
                    # but before the next INTEHEAD position (or end of file)
                    key_pos = None
                    next_intehead_pos = (
                        intehead_positions[timestep_idx + 1]
                        if timestep_idx + 1 < len(intehead_positions)
                        else file_size
                    )

                    if key in key_positions:
                        # Find the first key position that comes after this INTEHEAD
                        for pos in key_positions[key]:
                            if intehead_pos < pos < next_intehead_pos:
                                key_pos = pos
                                break

                    if key_pos is not None:
                        fid.seek(key_pos)
                        try:
                            # Read key data
                            header_size = struct.unpack(endian + "i", fid.read(4))[0]
                            key_name = (
                                fid.read(8).decode("ascii", errors="ignore").strip()
                            )
                            data_count = struct.unpack(endian + "i", fid.read(4))[0]
                            data_type = (
                                fid.read(4).decode("ascii", errors="ignore").strip()
                            )
                            end_size = struct.unpack(endian + "i", fid.read(4))[0]

                            if key_name == key and header_size == end_size:
                                # Read the data
                                raw_data = bytearray()
                                bytes_read = 0

                                # Determine bytes per element based on data type
                                if data_type == "CHAR":
                                    bytes_per_element = 8
                                else:
                                    bytes_per_element = 4

                                total_bytes_needed = data_count * bytes_per_element

                                while bytes_read < total_bytes_needed:
                                    chunk_size = struct.unpack(
                                        endian + "i", fid.read(4)
                                    )[0]
                                    chunk_data = fid.read(chunk_size)
                                    chunk_end = struct.unpack(
                                        endian + "i", fid.read(4)
                                    )[0]
                                    if chunk_size != chunk_end:
                                        break
                                    raw_data.extend(chunk_data)
                                    bytes_read += chunk_size

                                if len(raw_data) >= total_bytes_needed:
                                    if data_type == "CHAR":
                                        # Handle string data (like well names in ZWEL)
                                        if (
                                            len(raw_data) >= data_count * 8
                                        ):  # CHAR uses 8 bytes per element
                                            char_data = np.frombuffer(
                                                raw_data, dtype="S1"
                                            ).reshape((-1, 8))
                                            char_data = np.char.decode(
                                                char_data, encoding="ascii"
                                            ).astype(str)
                                            # Join characters to form complete strings
                                            string_data = np.array(
                                                [
                                                    "".join(row).strip()
                                                    for row in char_data
                                                ]
                                            )
                                            result[key] = string_data
                                        else:
                                            if (
                                                logger.getEffectiveLevel()
                                                <= logging.DEBUG
                                            ):
                                                logging.debug(
                                                    f"Insufficient CHAR data for {key}: expected {data_count * 8}, got {len(raw_data)}"
                                                )
                                    else:
                                        # Handle numeric data
                                        dtype_map = {
                                            "REAL": "f4",
                                            "DOUB": "f8",
                                            "INTE": "i4",
                                            "LOGI": "i4",
                                        }
                                        dtype = dtype_map.get(data_type, "f4")
                                        key_data = np.frombuffer(
                                            raw_data, dtype=endian + dtype
                                        )

                                        # For now, just use the data as-is without truncation

                                        result[key] = key_data

                        except Exception as e:
                            logging.error(
                                f"Error reading {key} for timestep {timestep_idx}: {e}"
                            )
                            # If reading fails, add empty data
                            if key in ["ZWEL"]:
                                result[key] = np.array([])  # Empty string array
                            else:
                                result[key] = np.array([])  # Empty numeric array
                    else:
                        # Key doesn't exist for this timestep, add empty data
                        if key in ["ZWEL"]:
                            result[key] = np.array([])  # Empty string array
                        else:
                            result[key] = np.array([])  # Empty numeric array

                all_results[timestep_idx] = result

        # If specific timestep requested, return only that one
        if tstep_id is not None:
            if tstep_id in all_results:
                return {tstep_id: all_results[tstep_id]}
            else:
                raise ValueError(f"Timestep {tstep_id} not found in {file_path}")

        # Transform results to the expected format
        def transform_results_dict(all_results: dict) -> dict:
            """Convert {tstep: {key: value}} -> {key: [values]}."""
            merged = {}
            for _, result in sorted(all_results.items()):
                for k, v in result.items():
                    if k not in merged:
                        merged[k] = []
                    merged[k].append(v)
            return merged

        return transform_results_dict(all_results)

    def _add_date_and_time(self, data: dict, prev_date=None, prev_days=0) -> dict:
        """Adds DATE and TIME fields to restart data if INTEHEAD exists."""

        result = dict(data)  # copy
        if "INTEHEAD" in data:
            header = data["INTEHEAD"]
            day, mon, year = header[64], header[65], header[66]
            try:
                date = datetime(year, mon, day)
                result["DATE"] = date
                result["TIME"] = (date - prev_date).days + prev_days if prev_date else 0
            except Exception as e:
                logging.warning(f"Invalid date in INTEHEAD: {e}")
        return result

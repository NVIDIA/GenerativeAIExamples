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

# Copied from physicsnemo/examples/reservoir_simulation/sim_utils/ecl_reader.py
# Copyright 2025 Tsubasa Onishi, NVIDIA CORPORATION & AFFILIATES
# Licensed under the Apache License, Version 2.0
# https://github.com/NVIDIA/physicsnemo

import numpy as np
import struct
import os
import logging
import glob
from datetime import datetime

logger = logging.getLogger(__name__)


def _find_file(base: str, ext: str) -> str:
    """Find file with case-insensitive extension (e.g. .INIT or .init)."""
    for suffix in [ext.upper(), ext.lower()]:
        path = f"{base}.{suffix}"
        if os.path.exists(path):
            return path
    return f"{base}.{ext.upper()}"


class EclReader:
    """Reads SLB ECLIPSE style binary output files (.INIT, .EGRID, .UNRST, .X00xx, .SMSPEC, .UNSMRY)."""

    def __init__(self, input_file_path: str) -> None:
        self.input_file_path = input_file_path
        self._validate_input_file()
        self._initialize_file_names()

    def read_init(self, keys: list = None) -> dict:
        """Reads data from the initial conditions file (.INIT)."""
        return self._read_bin(self.init_file_path, keys)

    def read_egrid(self, keys: list = None) -> dict:
        """Reads data from the grid data file (.EGRID)."""
        return self._read_bin(self.egrid_file_path, keys)

    def read_restart(self, keys: list = None, tstep_id: int = None) -> dict:
        """Reads restart data from .UNRST or .X00xx files."""
        unified_file = _find_file(self.input_file_path_base, "UNRST")
        if os.path.exists(unified_file):
            return self._read_unrst(unified_file, keys, tstep_id)

        base_dir = os.path.dirname(self.input_file_path_base)
        base_name = os.path.basename(self.input_file_path_base)
        search_pattern = os.path.join(base_dir, f"{base_name}.X[0-9][0-9][0-9][0-9]")
        files = sorted(glob.glob(search_pattern))

        if not files:
            raise FileNotFoundError("No restart files (.UNRST or .X00xx) were found.")

        if tstep_id is not None:
            match_file = f"{self.input_file_path_base}.X{self._int2ext(tstep_id)}"
            if not os.path.exists(match_file):
                raise FileNotFoundError(f"Restart file not found: {match_file}")
            data = self._read_bin(match_file, keys)
            result = self._add_date_and_time(data)
            return {tstep_id: result}

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
        """Reads summary data from .UNSMRY or .Sxxxx files for fields, wells, or groups."""
        smspec_file = _find_file(self.input_file_path_base, "SMSPEC")
        if not os.path.exists(smspec_file):
            raise FileNotFoundError(f"Summary specification file not found: {smspec_file}")

        with open(smspec_file, "rb") as fid:
            file_data = fid.read()

        first_int = struct.unpack("<i", file_data[:4])[0]
        endian = "<" if (first_int > 0 and first_int < 1000) else ">"

        keywords_pos = file_data.find(b"KEYWORDS")
        wgnames_pos = file_data.find(b"WGNAMES")
        names_pos = file_data.find(b"NAMES")

        if keywords_pos == -1:
            raise ValueError("KEYWORDS record not found in SMSPEC file")

        keywords_pos -= 4
        with open(smspec_file, "rb") as fid:
            fid.seek(keywords_pos)
            raw_keys, n_key = self._read_smspec_record(fid, endian)

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
            raise ValueError(f"Mismatch between keys ({n_key}) and entities ({n_ent}) in .SMSPEC.")

        all_keys = ["".join(row).strip() for row in raw_keys]
        all_entities = ["".join(row).strip() for row in raw_entities]

        if entities is None:
            entities = sorted(set(all_entities))

        n_keys = len(keys)
        n_ents = len(entities)

        index_map = {
            (k, e): i
            for i, (k, e) in enumerate(zip(all_keys, all_entities))
            if k in keys and e in entities
        }

        time_series = []
        summary_data = []

        unsmry_file = _find_file(self.input_file_path_base, "UNSMRY")
        files = [unsmry_file] if os.path.exists(unsmry_file) else []
        if not files:
            base_dir = os.path.dirname(self.input_file_path_base)
            base_name = os.path.basename(self.input_file_path_base)
            pattern = os.path.join(base_dir, f"{base_name}.S[0-9][0-9][0-9][0-9]")
            files = sorted(glob.glob(pattern))

        for fname in files:
            if not os.path.exists(fname):
                continue

            with open(fname, "rb") as fid:
                self._load_vector(fid, endian)

                while True:
                    _, _, label = self._load_vector(fid, endian)
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

        time_series = np.array(time_series)
        summary_data = np.array(summary_data)

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

    def list_smry_keys(self) -> list:
        """Return sorted list of unique summary keys available in SMSPEC (e.g. FOPR, FOPT, TIME)."""
        smspec_file = _find_file(self.input_file_path_base, "SMSPEC")
        if not os.path.exists(smspec_file):
            raise FileNotFoundError(f"Summary specification file not found: {smspec_file}")
        with open(smspec_file, "rb") as fid:
            file_data = fid.read()
        first_int = struct.unpack("<i", file_data[:4])[0]
        endian = "<" if (first_int > 0 and first_int < 1000) else ">"
        keywords_pos = file_data.find(b"KEYWORDS")
        if keywords_pos == -1:
            raise ValueError("KEYWORDS record not found in SMSPEC file")
        keywords_pos -= 4
        with open(smspec_file, "rb") as fid:
            fid.seek(keywords_pos)
            raw_keys, _ = self._read_smspec_record(fid, endian)
        all_keys = ["".join(row).strip() for row in raw_keys]
        return sorted(set(all_keys))

    def read_smry_vectors(self, keys: list) -> dict:
        """Read summary vectors for given keys. Returns dict key -> np.array (field-level). ESmry-compatible."""
        smry = self.read_smry(keys=keys, entities=None)
        result = {}
        time_arr = np.asarray(smry.get("TIME", np.array([])))
        result["TIME"] = time_arr
        for key in keys:
            for ent, block in smry.items():
                if ent == "TIME":
                    continue
                if isinstance(block, dict) and key in block:
                    result[key] = np.asarray(block[key])
                    break
        return result

    def get_smry_length(self) -> int:
        """Return number of report steps in summary. Returns 1 if unavailable."""
        try:
            smry = self.read_smry(keys=["FOPR", "FOPT", "TIME"], entities=None)
            time_arr = np.asarray(smry.get("TIME", np.array([])))
            return len(time_arr) if time_arr.size > 0 else 1
        except Exception:
            return 1

    def get_last_restart_step(self) -> int:
        """
        Return last report step from restart files. Uses UNRST if present, else X0001/X0002/...
        Returns 1 if no restart files found.
        """
        # 1) Check UNRST
        unified_file = _find_file(self.input_file_path_base, "UNRST")
        if os.path.exists(unified_file):
            try:
                with open(unified_file, "rb") as fid:
                    file_data = fid.read()
                intehead_positions = []
                pos = 0
                while True:
                    pos = file_data.find(b"INTEHEAD", pos)
                    if pos == -1:
                        break
                    intehead_positions.append(pos - 4)
                    pos += 8
                if intehead_positions:
                    return len(intehead_positions) - 1  # 0-indexed
            except Exception:
                pass
        # 2) Check X0001, X0002, ...
        base_dir = os.path.dirname(self.input_file_path_base)
        base_name = os.path.basename(self.input_file_path_base)
        search_pattern = os.path.join(base_dir, f"{base_name}.X[0-9][0-9][0-9][0-9]")
        files = sorted(glob.glob(search_pattern))
        if files:
            try:
                tsteps = [int(os.path.basename(f).split("X")[-1]) for f in files]
                return max(tsteps) if tsteps else 1
            except (ValueError, OSError):
                pass
        return 1

    def _validate_input_file(self) -> None:
        base, ext = os.path.splitext(self.input_file_path)
        ext_upper = ext.upper()
        if ext_upper in [".SMSPEC", ".UNSMRY"]:
            self.input_file_path_base = base
            return
        if not os.path.exists(self.input_file_path):
            raise FileNotFoundError(f"Input file not found: {self.input_file_path}")
        if ext_upper not in [".DATA", ".AFI"]:
            raise RuntimeError(f"Unsupported input file: {self.input_file_path}")
        self.input_file_path_base = base

    def _initialize_file_names(self) -> None:
        self.init_file_path = _find_file(self.input_file_path_base, "INIT")
        self.egrid_file_path = _find_file(self.input_file_path_base, "EGRID")
        self.unrst_file_path = f"{self.input_file_path_base}.UNRST"

    def _read_bin(self, file_path: str, keys: list) -> dict:
        if keys is None:
            return {}

        variables = {}
        with open(file_path, "rb") as fid:
            endian = self._detect_endian(fid)
            found_keys = {key: False for key in keys}

            while keys and not all(found_keys.values()):
                data, _, key = self._load_vector(fid, endian)
                key = key.strip()
                if key in found_keys:
                    if isinstance(data, np.ndarray):
                        variables[key] = data
                    elif isinstance(data, (bytes, str)):
                        variables[key] = data.decode(errors="ignore").strip() if isinstance(data, bytes) else data
                    elif isinstance(data, (int, float)):
                        variables[key] = np.array([data], dtype=np.float32)
                    else:
                        variables[key] = data
                    found_keys[key] = True

                if fid.tell() >= os.fstat(fid.fileno()).st_size:
                    break

            for key in keys:
                if key not in variables:
                    variables[key] = np.array([])

        return variables

    def _load_vector(self, fid, endian):
        try:
            header_size = struct.unpack(endian + "i", fid.read(4))[0]
            key = fid.read(8).decode(errors="ignore").strip()
            data_count = struct.unpack(endian + "i", fid.read(4))[0]
            data_type = fid.read(4).decode(errors="ignore").strip().upper()
            end_size = struct.unpack(endian + "i", fid.read(4))[0]

            if header_size != end_size:
                return None, None, key

            dtype_map = {"CHAR": "S1", "INTE": "i4", "REAL": "f4", "DOUB": "f8", "LOGI": "i4"}
            dtype = dtype_map.get(data_type)

            if dtype:
                raw_data = bytearray()
                read_count = 0

                while read_count < data_count:
                    chunk_size = struct.unpack(endian + "i", fid.read(4))[0]
                    chunk_data = fid.read(chunk_size)
                    chunk_end = struct.unpack(endian + "i", fid.read(4))[0]
                    if chunk_size != chunk_end:
                        return None, None, key
                    raw_data.extend(chunk_data)
                    read_count += chunk_size // np.dtype(dtype).itemsize

                if data_type == "CHAR":
                    char_array = np.frombuffer(raw_data, dtype="S1").reshape((-1, 8))
                    char_array = np.char.decode(char_array, encoding="utf-8").astype(str)
                    return char_array, data_count, key
                else:
                    data = np.frombuffer(raw_data, dtype=endian + dtype)
                    return data, data_count, key
            else:
                fid.seek(data_count * 4, os.SEEK_CUR)
                return None, None, key
        except struct.error:
            return None, None, ""

    def _read_smspec_record(self, fid, endian):
        try:
            header_size = struct.unpack(endian + "i", fid.read(4))[0]
            key = fid.read(8).decode("ascii", errors="ignore").strip()
            data_count = struct.unpack(endian + "i", fid.read(4))[0]
            data_type = fid.read(4).decode("ascii", errors="ignore").strip()
            end_size = struct.unpack(endian + "i", fid.read(4))[0]

            if header_size != end_size:
                raise ValueError(f"Header size mismatch for {key}")

            if data_count <= 0:
                return np.array([]), 0

            if data_type == "CHAR":
                bytes_per_element = 8
            else:
                dtype_map = {"INTE": "i4", "REAL": "f4", "DOUB": "f8", "LOGI": "i4"}
                dtype = dtype_map.get(data_type, "i4")
                bytes_per_element = np.dtype(dtype).itemsize

            raw_data = bytearray()
            bytes_read = 0
            total_bytes_needed = data_count * bytes_per_element

            while bytes_read < total_bytes_needed:
                chunk_size = struct.unpack(endian + "i", fid.read(4))[0]
                chunk_data = fid.read(chunk_size)
                chunk_end = struct.unpack(endian + "i", fid.read(4))[0]
                if chunk_size != chunk_end:
                    raise ValueError("Chunk size mismatch")
                raw_data.extend(chunk_data)
                bytes_read += chunk_size

            if data_type == "CHAR":
                if len(raw_data) >= total_bytes_needed:
                    char_data = np.frombuffer(raw_data, dtype="S1").reshape((-1, 8))
                    char_data = np.char.decode(char_data, encoding="ascii").astype(str)
                    return char_data, data_count
                raise ValueError("Insufficient CHAR data")
            else:
                dtype_map = {"INTE": "i4", "REAL": "f4", "DOUB": "f8", "LOGI": "i4"}
                dtype = dtype_map.get(data_type, "i4")
                if len(raw_data) >= total_bytes_needed:
                    data = np.frombuffer(raw_data, dtype=endian + dtype)
                    return data, data_count
                raise ValueError("Insufficient data")

        except Exception as e:
            raise RuntimeError(f"Error reading SMSPEC record: {e}")

    def _detect_endian(self, fid):
        fid.seek(0)
        test_int = fid.read(4)
        little_endian = struct.unpack("<i", test_int)[0]
        big_endian = struct.unpack(">i", test_int)[0]
        fid.seek(0)
        return "<" if abs(little_endian) < abs(big_endian) else ">"

    def _int2ext(self, i):
        return f"{i:04d}"

    def _read_unrst(self, file_path: str, keys: list = None, tstep_id: int = None) -> dict:
        if keys is None:
            keys = []

        all_results = {}
        file_size = os.path.getsize(file_path)

        with open(file_path, "rb") as fid:
            file_data = fid.read()

        first_int = struct.unpack("<i", file_data[:4])[0]
        endian = "<" if (first_int > 0 and first_int < 1000) else ">"

        intehead_positions = []
        pos = 0
        while True:
            pos = file_data.find(b"INTEHEAD", pos)
            if pos == -1:
                break
            intehead_positions.append(pos - 4)
            pos += 8

        key_positions = {key: [] for key in keys} if keys else {}
        for key in keys:
            pos = 0
            while True:
                pos = file_data.find(key.encode("ascii"), pos)
                if pos == -1:
                    break
                if pos >= 4:
                    try:
                        header_size = struct.unpack(endian + "i", file_data[pos - 4 : pos])[0]
                        if 8 <= header_size <= 1000:
                            key_positions[key].append(pos - 4)
                    except (struct.error, IndexError):
                        pass
                pos += len(key)

        with open(file_path, "rb") as fid:
            dates = []
            times = []

            for intehead_pos in intehead_positions:
                fid.seek(intehead_pos)
                try:
                    header_size = struct.unpack(endian + "i", fid.read(4))[0]
                    key = fid.read(8).decode("ascii", errors="ignore").strip()
                    data_count = struct.unpack(endian + "i", fid.read(4))[0]
                    data_type = fid.read(4).decode("ascii", errors="ignore").strip()
                    end_size = struct.unpack(endian + "i", fid.read(4))[0]

                    if key == "INTEHEAD" and header_size == end_size:
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
                                dates.append(datetime(IYEAR, IMON, IDAY))
                            else:
                                raise ValueError("INTEHEAD data too short")
                        else:
                            raise ValueError("Failed to read INTEHEAD")
                    else:
                        raise ValueError("Invalid INTEHEAD record")
                except Exception as e:
                    raise RuntimeError(f"Error reading INTEHEAD: {e}")

            times = []
            if dates:
                base_date = dates[0]
                for date in dates:
                    time_delta = date - base_date
                    times.append(time_delta.total_seconds() / (24 * 3600))

            for timestep_idx, (intehead_pos, date, time) in enumerate(zip(intehead_positions, dates, times)):
                result = {"DATE": date, "TIME": time}

                fid.seek(intehead_pos)
                try:
                    header_size = struct.unpack(endian + "i", fid.read(4))[0]
                    key = fid.read(8).decode("ascii", errors="ignore").strip()
                    data_count = struct.unpack(endian + "i", fid.read(4))[0]
                    data_type = fid.read(4).decode("ascii", errors="ignore").strip()
                    end_size = struct.unpack(endian + "i", fid.read(4))[0]

                    if key == "INTEHEAD" and header_size == end_size:
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
                            result["INTEHEAD"] = np.frombuffer(raw_data, dtype=endian + "i4")
                        else:
                            result["INTEHEAD"] = np.array([])
                    else:
                        result["INTEHEAD"] = np.array([])
                except Exception:
                    result["INTEHEAD"] = np.array([])

                next_intehead_pos = intehead_positions[timestep_idx + 1] if timestep_idx + 1 < len(intehead_positions) else file_size

                for key in keys:
                    if key == "INTEHEAD":
                        continue

                    key_pos = None
                    if key in key_positions:
                        for p in key_positions[key]:
                            if intehead_pos < p < next_intehead_pos:
                                key_pos = p
                                break

                    if key_pos is not None:
                        fid.seek(key_pos)
                        try:
                            header_size = struct.unpack(endian + "i", fid.read(4))[0]
                            key_name = fid.read(8).decode("ascii", errors="ignore").strip()
                            data_count = struct.unpack(endian + "i", fid.read(4))[0]
                            data_type = fid.read(4).decode("ascii", errors="ignore").strip()
                            end_size = struct.unpack(endian + "i", fid.read(4))[0]

                            if key_name == key and header_size == end_size:
                                raw_data = bytearray()
                                bytes_read = 0
                                bytes_per_element = 8 if data_type == "CHAR" else 4
                                total_bytes_needed = data_count * bytes_per_element

                                while bytes_read < total_bytes_needed:
                                    chunk_size = struct.unpack(endian + "i", fid.read(4))[0]
                                    chunk_data = fid.read(chunk_size)
                                    chunk_end = struct.unpack(endian + "i", fid.read(4))[0]
                                    if chunk_size != chunk_end:
                                        break
                                    raw_data.extend(chunk_data)
                                    bytes_read += chunk_size

                                if len(raw_data) >= total_bytes_needed:
                                    if data_type == "CHAR":
                                        char_data = np.frombuffer(raw_data, dtype="S1").reshape((-1, 8))
                                        char_data = np.char.decode(char_data, encoding="ascii").astype(str)
                                        result[key] = np.array(["".join(row).strip() for row in char_data])
                                    else:
                                        dtype_map = {"REAL": "f4", "DOUB": "f8", "INTE": "i4", "LOGI": "i4"}
                                        dtype = dtype_map.get(data_type, "f4")
                                        result[key] = np.frombuffer(raw_data, dtype=endian + dtype)
                                else:
                                    result[key] = np.array([])
                            else:
                                result[key] = np.array([])
                        except Exception:
                            result[key] = np.array([])
                    else:
                        result[key] = np.array([])

                all_results[timestep_idx] = result

        if tstep_id is not None:
            if tstep_id in all_results:
                return {tstep_id: all_results[tstep_id]}
            raise ValueError(f"Timestep {tstep_id} not found")

        def transform_results_dict(all_results: dict) -> dict:
            merged = {}
            for _, result in sorted(all_results.items()):
                for k, v in result.items():
                    if k not in merged:
                        merged[k] = []
                    merged[k].append(v)
            return merged

        return transform_results_dict(all_results)

    def _add_date_and_time(self, data: dict, prev_date=None, prev_days=0) -> dict:
        result = dict(data)
        if "INTEHEAD" in data:
            header = data["INTEHEAD"]
            day, mon, year = header[64], header[65], header[66]
            try:
                date = datetime(year, mon, day)
                result["DATE"] = date
                result["TIME"] = (date - prev_date).days + prev_days if prev_date else 0
            except Exception:
                pass
        return result

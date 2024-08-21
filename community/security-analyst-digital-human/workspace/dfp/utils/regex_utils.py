# SPDX-FileCopyrightText: Copyright (c) 2022-2024, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import re

# pylint: disable=invalid-name
iso_date_regex_pattern = (
    # YYYY-MM-DD
    r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})"
    # Start of time group (must match everything to add fractional days)
    r"(?:T"
    # HH
    r"(?P<hour>\d{1,2})"
    # : or _ or .
    r"(?::|_|\.)"
    # MM
    r"(?P<minute>\d{1,2})"
    # : or _ or .
    r"(?::|_|\.)"
    # SS
    r"(?P<second>\d{1,2})"
    # Optional microseconds (don't capture the period)
    r"(?:\.(?P<microsecond>\d{0,6}))?"
    # End of time group (optional)
    r")?"
    # Optional Zulu time
    r"(?P<zulu>Z)?")

iso_date_regex = re.compile(iso_date_regex_pattern)

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

import logging

__all__ = ["Completion", "Well"]


def __dir__():
    return __all__


class Completion:
    """Represents a well completion.

    A completion defines a connection between a well and a grid cell.  It stores
    information about the completion's location, status (open or shut), and
    flow direction.

    Attributes:
        I (int): I-index of the grid cell (1-based).
        J (int): J-index of the grid cell (1-based).
        K (int): K-index of the grid cell (1-based).
        status (str): Completion status ("OPEN" or "SHUT").
        dir (int): Penetration direction (1=X-dir, 2=Y-dir, 3=Z-dir, 4=fractured in X-dir, 5=fractured in Y-dir).
        connection_factor (float): Connection transmissibility factor.
        IJK (int, optional): Linear index of the grid cell (1-based). Set dynamically
            via `set_ijk()` method. May not exist until explicitly set.
        flow_rate (float, optional): Flow rate at the completion. Positive: injection,
            negative: production. Set dynamically via `set_flow_rate()` method.
            May not exist until explicitly set.
    """

    def __init__(
        self, I: int, J: int, K: int, dir: int, stat: int, conx_factor: float
    ) -> None:
        """Initializes a Completion object.

        Parameters
            I (int): I-index of the grid cell (1-based).
            J (int): J-index of the grid cell (1-based).
            K (int): K-index of the grid cell (1-based).
            dir (int): penetration direction. 1=X-dir, 2=Y-dir, 3=Z-dir, 4=fractured in X-dir, and 5=fractured in Y-dir.
            stat (int): Completion status ID (positive for open, other values for shut).
            conx_factor (float): Connection transmissibility factor
        """
        self.I = I
        self.J = J
        self.K = K
        self.dir = dir
        self._set_status(stat)
        self.connection_factor = conx_factor

    def set_ijk(self, ijk: int) -> None:
        """Sets the linear grid cell index (IJK).

        Parameters
            ijk (int): Linear index of the grid cell (1-based).
        """
        self.IJK = ijk

    def set_flow_rate(self, val: float) -> None:
        """Sets the flow rate at the completion.

        Parameters
            val (float): Flow rate. Positive: injection, negative: production.
        """
        self.flow_rate = val  # positive: injection, negative: production

    # ---- Private Methods ---------------------------------------------------------------------------------------------

    def _set_status(self, stat_id: int) -> None:
        """Sets the completion status.

        Parameters
            stat_id (int): Status ID (positive for open, other values for shut).
        """
        self.status = "OPEN" if stat_id > 0 else "SHUT"


class Well:
    """Represents a well.

    A well has a name, type (producer or injector), and a list of completions.

    Attributes:
        name (str): Name of the well.
        type (str): Type of well ("PRD" or "INJ").
        completions (list[Completion]): List of Completion objects associated with the well.
        num_active_completions (int): Number of active (open) completions.
    """

    def __init__(self, name: str, type_id: int, stat: int) -> None:
        """Initializes a Well object.

        Parameters
            name (str): Name of the well.
            type_id (int): Well type ID.
            stat (int): Well status ID (positive for open, other values for shut).
        """
        self.name = name
        self._set_type(type_id)
        self.completions = []
        self.num_active_completions = 0
        self.status = "OPEN" if stat > 0 else "SHUT"

    def add_completion(
        self, I: int, J: int, K: int, dir: int, stat: int, conx_factor: float
    ) -> None:
        """Adds a completion to the well.

        Parameters
            I (int): I-index of the grid cell (1-based).
            J (int): J-index of the grid cell (1-based).
            K (int): K-index of the grid cell (1-based).
            dir (int): penetration direction. 1=X-dir, 2=Y-dir, 3=Z-dir, 4=fractured in X-dir, and 5=fractured in Y-dir
            stat (int): Completion status ID (positive for open, other values for shut).
            conx_factor (float): Connection transmissibility factor
        """
        cmpl_stat = (
            stat if self.status == "OPEN" else 0
        )  # treatment for OPM (ICON is not updated when a well is shut)
        self.completions.append(Completion(I, J, K, dir, cmpl_stat, conx_factor))
        if self.completions[-1].status == "OPEN":
            self.num_active_completions += 1

    def set_status(self) -> None:
        """Set well status based on completion status"""
        self.status = "SHUT" if self.num_active_completions == 0 else "OPEN"

    # ---- Private Methods ---------------------------------------------------------------------------------------------

    def _set_type(self, type_id: int) -> None:
        """Sets the well type.

        Parameters
            type_id (int):
            - Well type ID - 1 for PRD, 2 for OILINJ, 3 for WATINJ, 4 for GASINJ (ECL)
            - 5 for injector identifier for CMG (unclear how to get different injector types in CMG)
        """
        if type_id == 1:
            self.type = "PRD"
        elif type_id in [2, 3, 4, 5]:
            self.type = "INJ"
        else:
            self.type = "UNKNOWN"
            logging.warning(f"Unknown well type: {type_id} found at well: {self.name}")

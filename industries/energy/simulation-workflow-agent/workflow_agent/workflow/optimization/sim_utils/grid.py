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
import logging

NUM_MAX_DIMENS = 3

# Module-level logger
logger = logging.getLogger(__name__)


class Grid:
    """Handles reservoir grid structure and operations.

    This class manages grid dimensions, active cells, cell center coordinates,
    connections/edges for graph construction, and transmissibilities.
    """

    FULL_GRID_KEYS = ["PORV"]

    def __init__(self, init_data: dict, egrid_data: dict) -> None:
        self.nx, self.ny, self.nz = init_data["INTEHEAD"][8:11].astype(int).tolist()
        self.nn = self.nx * self.ny * self.nz
        self.num_max_dims = NUM_MAX_DIMENS
        self.single_layer = self.nz == 1
        self.porv = init_data["PORV"]
        self.actnum = (self.porv > 0).astype(int)
        self.actnum_bool = (self.porv > 0).astype(bool)
        self.nact = np.sum(self.actnum)
        self.X, self.Y, self.Z = self._set_cell_center_coord(egrid_data)
        self._initialize_tran_keys()
        self._set_dual_poro(dp_flag=egrid_data["FILEHEAD"][5])
        # NNC (Non-Neighbor Connections) are optional - not all datasets have them
        dict_NNC = {
            "NNC1": egrid_data.get("NNC1", np.array([])),
            "NNC2": egrid_data.get("NNC2", np.array([]))
        }
        self._set_NNC(dict_NNC=dict_NNC)
        self._compute_ijk_to_active_mapping()
        self._compute_connections()
        self._compute_total_tran(init_data)

    def ijk_from_I_J_K(self, I: int, J: int, K: int) -> int:
        return I + (J - 1) * self.nx + (K - 1) * self.nx * self.ny

    def get_conx_tran(self) -> tuple:
        """Get connections and transmissibilities for the grid.

        Returns
            tuple: A tuple containing (connections, transmissibilities) where
                connections is an array of grid cell connections and
                transmissibilities is the corresponding edge features.
        """
        # Validate edge indices are within valid range
        if self._conx.size > 0:
            max_idx = np.max(self._conx)
            if max_idx >= self.nact:
                print(
                    f"⚠️ Warning: Edge index {max_idx} >= nact ({self.nact}). This may cause issues."
                )
            if np.min(self._conx) < 0:
                print(
                    f"⚠️ Warning: Edge index {np.min(self._conx)} < 0. This may cause issues."
                )
        return self._conx, self._Txyz_flattened

    def _set_cell_center_coord(self, egrid_data: dict):
        """
        Compute cell center coordinates from COORD and ZCORN arrays (corner-point grid).

        Parameters
            coord (np.ndarray): shape (6, nx+1, ny+1), coordinates of grid pillars.
            zcorn (np.ndarray): shape (8 * nx * ny * nz,), raw ZCORN values (Fortran-ordered).
            nx, ny, nz (int): number of cells in each direction.

        Returns
            (center_x, center_y, center_z): 3D arrays of shape (nx, ny, nz) with cell centers.
        """
        if "COORD" not in egrid_data or "ZCORN" not in egrid_data:
            return np.array([]), np.array([]), np.array([])

        coord, zcorn = egrid_data["COORD"], egrid_data["ZCORN"]
        nx, ny, nz = self.nx, self.ny, self.nz

        # Reshape ZCORN into logical (2*nx, 2*ny, 2*nz) grid of corner depths
        coord = coord.reshape((6, nx + 1, ny + 1), order="F")
        zcorn = zcorn.reshape((2 * nx, 2 * ny, 2 * nz), order="F")

        center_X = np.zeros((nx, ny, nz))
        center_Y = np.zeros((nx, ny, nz))
        center_Z = np.zeros((nx, ny, nz))

        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    # Get the 4 pillars for this cell
                    pillars = [
                        coord[:, i, j],
                        coord[:, i + 1, j],
                        coord[:, i, j + 1],
                        coord[:, i + 1, j + 1],
                    ]

                    # Compute average X, Y from top and base of each pillar
                    x_vals = [
                        0.5 * (p[0] + p[3]) for p in pillars
                    ]  # avg top and base X
                    y_vals = [
                        0.5 * (p[1] + p[4]) for p in pillars
                    ]  # avg top and base Y

                    center_X[i, j, k] = np.mean(x_vals)
                    center_Y[i, j, k] = np.mean(y_vals)

                    # Collect 8 corner Z-values for this cell
                    z000 = zcorn[2 * i, 2 * j, 2 * k]
                    z100 = zcorn[2 * i + 1, 2 * j, 2 * k]
                    z010 = zcorn[2 * i, 2 * j + 1, 2 * k]
                    z110 = zcorn[2 * i + 1, 2 * j + 1, 2 * k]
                    z001 = zcorn[2 * i, 2 * j, 2 * k + 1]
                    z101 = zcorn[2 * i + 1, 2 * j, 2 * k + 1]
                    z011 = zcorn[2 * i, 2 * j + 1, 2 * k + 1]
                    z111 = zcorn[2 * i + 1, 2 * j + 1, 2 * k + 1]

                    center_Z[i, j, k] = np.mean(
                        [z000, z100, z010, z110, z001, z101, z011, z111]
                    )

        # active cell only vectors
        X = center_X.reshape(-1, order="F")[self.actnum_bool]
        Y = center_Y.reshape(-1, order="F")[self.actnum_bool]
        Z = center_Z.reshape(-1, order="F")[self.actnum_bool]

        return X, Y, Z

    def _initialize_tran_keys(self) -> None:
        """Initializes the transmissibility keys."""
        self._tran_keys = ["TRANX", "TRANY", "TRANZ", "TRANNNC"]

    def _set_dual_poro(self, dp_flag: int) -> None:
        """Configures the grid for dual porosity.

        Parameters
            dp_flag (int): Dual porosity flag (0 for single porosity, 1 or 2 for dual porosity).
        """
        self.dual_poro = dp_flag in [1, 2]
        if self.dual_poro and self.nz == 2:
            self.single_layer = True
        elif dp_flag not in [0, 1, 2]:
            print(
                f"Invalid dual porosity flag found: {dp_flag}. Proceeding with single porosity assumption."
            )

    def _set_NNC(self, dict_NNC: dict) -> None:
        """Configures the grid for NNCs.

        Parameters
            dict_NNC (dict): Dictionary containing egrid data (NNC1, NNC2).
        """
        self.NNC = dict_NNC["NNC1"].size > 0
        if self.NNC:
            self.NNC1 = dict_NNC["NNC1"]
            self.NNC2 = dict_NNC["NNC2"]
            self.num_NNCs = len(self.NNC1)
        else:
            self.NNC1, self.NNC2 = np.array([]), np.array([])
            self.num_NNCs = 0

    def _compute_ijk_to_active_mapping(self) -> None:
        """Compute mapping from IJK indices to active cell indices.
        This is static and can be reused across time steps.
        """
        self.ijk_to_active = {}
        active_idx = 0
        for ijk_linear in range(self.nn):
            if self.actnum[ijk_linear] > 0:
                self.ijk_to_active[ijk_linear] = active_idx
                active_idx += 1
        
        # Create 3D boolean mask for active cells (reshaped from 1D)
        self.actnum_3d = self.actnum_bool.reshape((self.nx, self.ny, self.nz), order="F")

    def _compute_connections(self) -> np.ndarray:
        """
        Computes the connection matrix.

        Returns
            np.ndarray: The connection matrix where each row represents a connection
            between two grid cells.

        Notes
            Indexing convention:
            - cell_idx_cumsum: 1-based sequential indices for active cells (1, 2, 3, ...)
            - NNC1/NNC2: 1-based ECLIPSE global cell indices
            - Final output (_conx): 0-based Python indices for active cells
        """

        # Compute active cell indexing: creates 1-based sequential indices (1, 2, 3, ...)
        # for active cells, 0 for inactive cells
        cell_idx = np.ones(self.nn, dtype=int)
        cell_idx[self.actnum == 0] = 0
        cell_idx_cumsum = np.cumsum(cell_idx)  # 1-based: active cells get 1, 2, 3, ...
        cell_idx_cumsum[self.actnum == 0] = 0  # Set inactive cells back to 0

        # Reshape active grid indices into 3D (maintains 1-based indexing)
        cell_idx_3D = cell_idx_cumsum.reshape(self.nx, self.ny, self.nz, order="F")

        # Extend face indexing by adding ghost layers (boundary cells remain 0)
        face_idx = np.zeros((self.nx + 2, self.ny + 2, self.nz + 2), dtype=int)
        face_idx[1 : self.nx + 1, 1 : self.ny + 1, 1 : self.nz + 1] = cell_idx_3D

        conx = []
        if self.nx > 1:  # X-direction connections
            idx1 = face_idx[: self.nx + 1, 1 : self.ny + 1, 1 : self.nz + 1]
            idx2 = face_idx[1 : self.nx + 2, 1 : self.ny + 1, 1 : self.nz + 1]
            conx.append(np.column_stack((idx1.ravel(order="F"), idx2.ravel(order="F"))))

        if self.ny > 1:  # Y-direction connections
            idx1 = face_idx[1 : self.nx + 1, : self.ny + 1, 1 : self.nz + 1]
            idx2 = face_idx[1 : self.nx + 1, 1 : self.ny + 2, 1 : self.nz + 1]
            conx.append(np.column_stack((idx1.ravel(order="F"), idx2.ravel(order="F"))))

        if not self.single_layer:  # Z-direction connections. Use this flag, instead of nz because nz = 2*nz in DP systems
            idx1 = face_idx[1 : self.nx + 1, 1 : self.ny + 1, : self.nz + 1]
            idx2 = face_idx[1 : self.nx + 1, 1 : self.ny + 1, 1 : self.nz + 2]
            conx.append(np.column_stack((idx1.ravel(order="F"), idx2.ravel(order="F"))))

        # Stack all connections into a single array
        conx = np.vstack(conx)

        # Non-neighboring connections (NNC)
        # NNC1/NNC2 are 1-based ECLIPSE global cell indices
        # We subtract 1 to convert to 0-based Python indices for array access
        # cell_idx_flattened then returns the 1-based sequential active cell index
        if self.NNC and self.NNC1.size > 0 and self.NNC2.size > 0:
            cell_idx_flattened = cell_idx_3D.ravel(order="F")
            NNC_conx = np.column_stack(
                (cell_idx_flattened[self.NNC1 - 1], cell_idx_flattened[self.NNC2 - 1])
            )
            conx = np.vstack((conx, NNC_conx))

        # Filter out boundary connections (connections involving inactive cells)
        # Inactive cells have index 0, so any connection with 0 is invalid
        self._valid_conx_idx = ~np.any(conx == 0, axis=1)

        # Filter boundary connections and convert to 0-based indexing
        # At this point, conx contains 1-based sequential active cell indices (1, 2, 3, ...)
        # We subtract 1 to convert to 0-based Python indices (0, 1, 2, ...) for final output
        self._conx = conx[self._valid_conx_idx] - 1

        # Log detailed grid and connection information at debug level
        if self._conx.size > 0 and logger.getEffectiveLevel() <= logging.DEBUG:
            total_cells = self.nx * self.ny * self.nz
            active_percentage = (self.nact / total_cells) * 100
            nnc_count = self.num_NNCs if hasattr(self, "num_NNCs") else 0

            logging.debug(
                f"Grid dimensions: {self.nx} × {self.ny} × {self.nz} = {total_cells:,} total cells"
            )
            logging.debug(
                f"Active cells: {self.nact:,} ({active_percentage:.1f}% of total)"
            )
            logging.debug(f"Connections: {self._conx.shape[0]:,} edges")
            logging.debug(
                f"  - Regular connections: {self._conx.shape[0] - nnc_count:,}"
            )
            logging.debug(f"  - NNC connections: {nnc_count:,}")
            logging.debug(
                f"Edge indices: min={np.min(self._conx)}, max={np.max(self._conx)}"
            )

    def _compute_total_tran(self, init_data: dict) -> None:
        """Computes and stores total transmissibility, including TRANNNC.

        Parameters
            init_data (dict): Dictionary of initialization data containing transmissibility keys.
        """
        # Check if any transmissibility keys exist in init_data
        available_tran_keys = [k for k in self._tran_keys if k in init_data]
        if not available_tran_keys:
            # Initialize transmissibility arrays as None if no tran data available
            self._Txyz_flattened = None
            self._T_xyz = None
            return

        nx, ny, nz = self.nx, self.ny, self.nz
        self._T_xyz = np.zeros((self.nn, self.num_max_dims))  # tran in xyz-dirs
        self._Tx = np.zeros((nx + 1, ny, nz))  # total tran in x-dir
        self._Ty = np.zeros((nx, ny + 1, nz))  # total tran in y-dir
        self._Tz = np.zeros((nx, ny, nz + 1))  # total tran in z-dir

        # Store phase tran at active cells
        for i, key in enumerate(self._tran_keys[:-1]):
            if key in init_data and init_data[key].size:
                self._T_xyz[self.actnum_bool, i] = init_data[key]

        # Compute total tran for xyz dirs
        Txyz_flattened = np.array([])
        if nx > 1:
            self._Tx[1 : nx + 1, :, :] = self._T_xyz[:, 0].reshape(
                nx, ny, nz, order="F"
            )
            Txyz_flattened = np.append(Txyz_flattened, self._Tx.ravel(order="F"))
        if ny > 1:
            self._Ty[:, 1 : ny + 1, :] = self._T_xyz[:, 1].reshape(
                nx, ny, nz, order="F"
            )
            Txyz_flattened = np.append(Txyz_flattened, self._Ty.ravel(order="F"))
        if not self.single_layer:
            self._Tz[:, :, 1 : nz + 1] = self._T_xyz[:, 2].reshape(
                nx, ny, nz, order="F"
            )
            Txyz_flattened = np.append(Txyz_flattened, self._Tz.ravel(order="F"))

        # Append total tran for NNCs if applicable
        if "TRANNNC" in init_data and init_data["TRANNNC"].size:
            Txyz_flattened = np.append(Txyz_flattened, init_data["TRANNNC"])

        self._Txyz_flattened = Txyz_flattened[self._valid_conx_idx]

    def create_completion_array(
        self, wells: dict, use_completion_connection_factor: bool = False
    ):
        """
        Create completion array from well data for a specific timestep.

        Parameters
        -----------
        wells : dict
            dict of Well objects for this sample

        Returns
        --------
        completion : np.ndarray
            Completion status array for active cells (1=injector, 0=closed, -1=producer)
        """
        completion_cell_id_inj = np.zeros(self.nact, dtype=float)
        completion_cell_id_prd = np.zeros(self.nact, dtype=float)
        ijk_to_active = self.ijk_to_active
        if not wells:
            return completion_cell_id_inj, completion_cell_id_prd
        for well_name in wells.keys():
            well = wells[well_name]
            if well.status == "OPEN":  # Only process open wells
                for completion_obj in well.completions:
                    if completion_obj.status == "OPEN":  # Only process open completions
                        ijk = completion_obj.IJK - 1  # Convert to 0-based indexing
                        if ijk in ijk_to_active:
                            active_idx = ijk_to_active[ijk]
                            cf = (
                                completion_obj.connection_factor
                                if use_completion_connection_factor
                                else 1.0
                            )
                            if well.type == "INJ":
                                completion_cell_id_inj[active_idx] = cf * 1.0
                            elif well.type == "PRD":
                                completion_cell_id_prd[active_idx] = cf * 1.0

        return completion_cell_id_inj, completion_cell_id_prd

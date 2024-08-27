# Copyright (c) 2022-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Converts DFP inference output to CSV for the purposes of visualization."""

import logging
import os
import typing

import mrc
import pandas as pd
from mrc.core import operators as ops

from morpheus.config import Config
from morpheus.io import serializers
from morpheus.messages.multi_ae_message import MultiAEMessage
from morpheus.pipeline.pass_thru_type_mixin import PassThruTypeMixin
from morpheus.pipeline.single_port_stage import SinglePortStage

logger = logging.getLogger(__name__)


class DFPVizPostprocStage(PassThruTypeMixin, SinglePortStage):
    """
    DFPVizPostprocStage performs post-processing on DFP inference output. The inference output is converted
    to input format expected by the DFP Visualization and saves to multiple files based on specified time
    period. Time period to group data by must be one of pandas' offset strings. The default period is one
    day (D). The output file will be named by appending period to prefix (e.g. dfp-viz-2022-08-30.csv).

    Parameters
    ----------
    c : `morpheus.config.Config`
        Pipeline configuration instance.
    period : str
        Time period to batch input data and save output files by. [default: `D`]
    output_dir : str
         Directory to which the output files will be written. [default: current directory]
    output_prefix : str
         Prefix for output files.
    """

    def __init__(self, config: Config, period: str = "D", output_dir: str = ".", output_prefix: str = "dfp-viz-"):
        super().__init__(config)

        self._user_column_name = config.ae.userid_column_name
        self._timestamp_column = config.ae.timestamp_column_name
        self._feature_columns = config.ae.feature_columns
        self._period = period
        self._output_dir = output_dir
        self._output_prefix = output_prefix
        self._output_filenames = []

    @property
    def name(self) -> str:
        """Unique name of the stage."""
        return "dfp-viz-postproc"

    def accepted_types(self) -> typing.Tuple:
        """
        Accepted input types for this stage are returned.

        Returns
        -------
        typing.Tuple[`morpheus.pipeline.messages.MultiAEMessage`, ]
            Accepted input types.

        """
        return (MultiAEMessage, )

    def supports_cpp_node(self):
        """Whether this stage supports a C++ node."""
        return False

    def _postprocess(self, x: MultiAEMessage) -> pd.DataFrame:

        viz_pdf = pd.DataFrame()
        viz_pdf[["user", "time"]] = x.get_meta([self._user_column_name, self._timestamp_column])
        datetimes = pd.to_datetime(viz_pdf["time"], errors='coerce')
        viz_pdf["period"] = datetimes.dt.to_period(self._period)

        for f in self._feature_columns:
            viz_pdf[f + "_score"] = x.get_meta(f + "_z_loss")

        viz_pdf["anomalyScore"] = x.get_meta("mean_abs_z")

        return viz_pdf

    def _write_to_files(self, x: MultiAEMessage):

        df = self._postprocess(x)

        unique_periods = df["period"].unique()

        for period in unique_periods:
            period_df = df[df["period"] == period]
            period_df = period_df.drop(["period"], axis=1)
            output_file = os.path.join(self._output_dir, self._output_prefix + str(period) + ".csv")

            is_first = False
            if output_file not in self._output_filenames:
                self._output_filenames.append(output_file)
                is_first = True

            lines = serializers.df_to_csv(period_df, include_header=is_first, include_index_col=False)
            os.makedirs(os.path.realpath(os.path.dirname(output_file)), exist_ok=True)
            with open(output_file, "a", encoding='UTF-8') as out_file:
                out_file.writelines(lines)

        return x

    def _build_single(self, builder: mrc.Builder, input_node: mrc.SegmentObject) -> mrc.SegmentObject:
        dfp_viz_postproc = builder.make_node(self.unique_name, ops.map(self._write_to_files))
        builder.make_edge(input_node, dfp_viz_postproc)

        return dfp_viz_postproc

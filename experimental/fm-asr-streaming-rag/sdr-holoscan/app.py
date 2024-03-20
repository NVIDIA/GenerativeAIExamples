# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""
Entrypoint for running SDR Holoscan pipeline
Ingests UDP packets with baseband I/Q data
"""

from holoscan.core import Application
from queue import Queue

from common import PARAM_FILE, FRONTEND_URI, DATABASE_URI, wait_for_uri
from riva_asr import RivaThread
import operators as op

class AsrStreamingApp(Application):
    def __init__(self):
        super().__init__()
        self.pcm_buffer = Queue()  # shared between PcmToAsrOp and RivaThread

    def compose(self):
        # Data ingest operators
        network_rx = op.BasicNetworkRxOp(self, name="network_rx", **self.kwargs("network_rx"))
        pkt_format = op.PacketFormatterOp(self, name="pkt_format", **self.kwargs("pkt_format"))

        # Signal processing operators
        lowpassfilt = op.LowPassFilterOp(self, name="lowpassfilt", **self.kwargs("lowpassfilt"))
        demodulate  = op.DemodulateOp(self, name="demodulate")
        resample    = op.ResampleOp(self, name="resample", **self.kwargs("resample"))
        pcm_to_asr  = op.PcmToAsrOp(self, self.pcm_buffer, name="pcm_to_asr")

        # Application flow
        self.add_flow(network_rx,  pkt_format,  {("burst_out", "burst_in")})
        self.add_flow(pkt_format,  lowpassfilt, {("signal_out", "signal_in")})
        self.add_flow(lowpassfilt, demodulate,  {("signal_out", "signal_in")})
        self.add_flow(demodulate,  resample,    {("signal_out", "signal_in")})
        self.add_flow(resample,    pcm_to_asr,  {("signal_out", "signal_in")})

    def run(self):
        # Wait for connections
        wait_for_uri(self.kwargs("riva")["uri"])
        wait_for_uri(FRONTEND_URI)
        wait_for_uri(DATABASE_URI)

        # Start Riva thread
        self.riva_handler = RivaThread(
            self.pcm_buffer,
            self.kwargs("riva"),
            frontend_uri=FRONTEND_URI,
            database_uri=DATABASE_URI
        )
        self.riva_handler.start()

        # Run application
        super().run()

        # Stop Riva thread
        self.riva_handler.stop()
        self.riva_handler.join()

if __name__ == "__main__":
    app = AsrStreamingApp()
    app.config(PARAM_FILE)
    app.run()
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

import time
import socket
import copy

from enum import Enum

import cupy as cp
import cupyx.scipy.signal as cusignal
import riva.client.proto.riva_asr_pb2 as rasr

from holoscan.core import Operator, OperatorSpec
from common import setup_logging, SignalEmission


class L4Proto(Enum):
    TCP = 0
    UDP = 1

class NetworkOpBurstParams:
    header: bytearray
    data: bytearray
    def reset(self):
        self.header = bytearray()
        self.data = bytearray()
    def __init__(self):
        self.reset()

def fm_demod(x: cp.array, axis=-1):
    """ Demodulate Frequency Modulated Signal
    """
    x = cp.asarray(x)
    if cp.isrealobj(x):
        raise AssertionError("Input signal must be complex-valued")
    x_angle = cp.unwrap(cp.angle(x), axis=axis)
    y = cp.diff(x_angle, axis=axis)
    return y

def lowpass(taps: cp.array, x: cp.array):
    return cusignal.lfilter(taps, cp.array([1]), x).astype(cp.complex64)

def reduce_fraction(numerator: int, denominator: int, max_up=1):
    max_freq = numerator * float(max_up)
    if max_freq > 10_000_000: # 10 MHz
        raise ValueError(f"max_freq {max_freq} is too high")

    out_freq_sf = round(max_freq / denominator)
    return max_up, out_freq_sf

def float_to_pcm(f_data: cp.array, dtype=cp.int16):
    """
    Function made using the following sources:
    - https://stackoverflow.com/a/15094612
    - https://stackoverflow.com/a/61835960
    - http://blog.bjornroche.com/2009/12/int-float-int-its-jungle-out-there.html
    """
    dtype_max = cp.iinfo(dtype).max
    dtype_min = cp.iinfo(dtype).min
    abs_int_max = 2**(cp.iinfo(dtype).bits -1)
    return cp.clip(f_data*abs_int_max, dtype_min, dtype_max).astype(cp.int16)


class BasicNetworkRxOp(Operator):
    sock_fd: socket.socket = None
    l4_proto: L4Proto = None
    ip_addr: str = None
    dst_port: int = None
    batch_size: int = None
    max_payload_size: int = None
    connected: bool = False
    send_burst: NetworkOpBurstParams = NetworkOpBurstParams()

    def initialize(self):
        Operator.initialize(self)
        try:
            if self.l4_proto == "udp":
                self.l4_proto = L4Proto.UDP
                self.sock_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                buffersize = 49_000_000
                self.sock_fd.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffersize)
            else:
                self.l4_proto = L4Proto.TCP
                self.sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            self.sock_fd.bind((self.ip_addr, self.dst_port))
            if self.l4_proto == L4Proto.TCP:
                self.sock_fd.listen(1)

            self.logger.info(f"Successfully listening on {self.ip_addr}:{self.dst_port}")
        except socket.error:
            self.logger.error("Failed to create socket")

        self.logger.info("Basic RX operator initialized")

    def __init__(self, fragment, *args, **kwargs):
        super().__init__(fragment, *args, **kwargs)
        self.logger = setup_logging(self.name)

    def setup(self, spec: OperatorSpec):
        # Settings
        spec.param("ip_addr")
        spec.param("dst_port")
        spec.param("l4_proto")
        spec.param("batch_size")
        spec.param("header_bytes")
        spec.param("max_payload_size")
        spec.output("burst_out")

    def compute(self, op_input, op_output, context):
        """
        Input is a TCP/UDP stream not directly managed by holoscan
        burst_out : NetworkOpBurstParams
        burst_out : bytearray
        """
        if self.l4_proto == L4Proto.TCP and not self.connected:
            try:
                self.sock_fd.settimeout(1)
                self.conn, self.addr = self.sock_fd.accept()
                self.logger.info(f"Connected by {self.addr}")
                self.connected = True
            except socket.error:
                return
            finally:
                self.sock_fd.settimeout(None)

        while True:
            try:
                if self.l4_proto == L4Proto.UDP:
                    tmp = self.sock_fd.recvfrom(self.max_payload_size, socket.MSG_DONTWAIT)
                    n = tmp[0]
                else:
                    n = self.conn.recv(self.max_payload_size, socket.MSG_DONTWAIT)
                # Seperate header and payload
                header, data = n[:self.header_bytes], n[self.header_bytes:]
            except BlockingIOError:
                if len(self.send_burst.data) > 0:
                    break
                else:
                    return

            if len(n) > 0:
                self.send_burst.header.extend(header)
                self.send_burst.data.extend(data)
            else:
                return

            if len(self.send_burst.data) >= self.batch_size:
                tmp = copy.deepcopy(self.send_burst)
                op_output.emit(tmp, "burst_out")
                self.send_burst.reset()
                return


class PacketFormatterOp(Operator):
    """ Format data from packets into a CuPy array and emit downstream with SignalEmission
    """
    def __init__(self, fragment, *args, **kwargs):
        super().__init__(fragment, *args, **kwargs)
        self.sample_rate_in = fragment.kwargs("sensor")["sample_rate"]
        self.logger = setup_logging(self.name)
        self.prev_log_time = None
        self.bytes_sent = 0

    def setup(self, spec: OperatorSpec):
        spec.param("log_period")
        spec.input("burst_in")    # bytearray
        spec.output("signal_out") # configurable

    def compute(self, op_input, op_output, context):
        """ Just copy data to a GPU CuPy array and emit
        """
        burst_in = op_input.receive("burst_in")

        # Copy data and emit
        data = cp.frombuffer(burst_in.data, dtype=cp.complex64)
        signal_out = SignalEmission(data, self.sample_rate_in)
        op_output.emit(signal_out, "signal_out")

        # Log emission every N seconds
        self.bytes_sent += len(burst_in.data)
        tnow = time.time()
        if not self.prev_log_time:
            self.prev_log_time = tnow
            return

        dt = tnow - self.prev_log_time
        if dt > self.log_period:
            bw = self.bytes_sent / dt / 1e6
            self.logger.info(f"Ingest bandwidth {bw:.2f} MB/s")
            self.bytes_sent = 0
            self.prev_log_time = tnow


class LowPassFilterOp(Operator):
    """ Design and apply an FIR lowpass filter using a Hamming window.
    """
    @classmethod
    def _jit_compile(cls, numtaps, cutoff, fs):
        taps = cusignal.firwin(numtaps, cutoff=cutoff, window="hamming", fs=fs)
        lowpass(taps, cp.ones(1000, dtype=cp.complex64))

    def __init__(self, fragment, *args, **kwargs):
        super().__init__(fragment, *args, **kwargs)
        self.logger = setup_logging(self.name)

        # JIT compile of filter
        self.logger.info("Doing JIT compilation")
        self.sample_rate_in = float(fragment.kwargs("sensor")["sample_rate"])
        LowPassFilterOp._jit_compile(
            int(kwargs["numtaps"]), float(kwargs["cutoff"]), self.sample_rate_in
        )

    def setup(self, spec: OperatorSpec):
        spec.param("cutoff")
        spec.param("numtaps")
        spec.input("signal_in")
        spec.output("signal_out")

    def initialize(self):
        Operator.initialize(self)
        self.cutoff = float(self.cutoff)
        self.numtaps = int(self.numtaps)
        self.taps = cusignal.firwin(
            self.numtaps, cutoff=self.cutoff, window="hamming", fs=self.sample_rate_in
        )

    def compute(self, op_input, op_output, context):
        signal_in = op_input.receive("signal_in")

        # Do work and emit
        data = lowpass(self.taps, signal_in.data)
        signal_out = SignalEmission(data, self.sample_rate_in)
        op_output.emit(signal_out, "signal_out")


class DemodulateOp(Operator):
    """ Do FM demodulation using discrete time differentiator
    """
    @classmethod
    def _jit_compile(cls):
        fm_demod(cp.ones(1000, dtype=cp.complex64))

    def __init__(self, fragment, *args, **kwargs):
        super().__init__(fragment, *args, **kwargs)
        self.logger = setup_logging(self.name)

        # JIT compile of demodulation
        self.logger.info("Doing JIT compilation")
        DemodulateOp._jit_compile()

    def setup(self, spec: OperatorSpec):
        spec.input("signal_in")
        spec.output("signal_out")

    def compute(self, op_input, op_output, context):
        signal_in = op_input.receive("signal_in")

        # Do work and emit
        data = fm_demod(signal_in.data)
        signal_out = SignalEmission(data, signal_in.fs)
        op_output.emit(signal_out, "signal_out")


class ResampleOp(Operator):
    """ Up-sample or down-sample signal based on input
    """
    @classmethod
    def _jit_compile(cls):
        t_sig = cp.ones([int(1024*250e3//16e3)], dtype=cp.float32)
        cusignal.resample_poly(t_sig, 1, 2, window="hamming")

    def __init__(self, fragment, *args, **kwargs):
        super().__init__(fragment, *args, **kwargs)
        self.logger = setup_logging(self.name)

        # JIT compile resampling
        self.logger.info("Doing JIT compilation")
        ResampleOp._jit_compile()

    def setup(self, spec: OperatorSpec):
        spec.param("sample_rate_out")
        spec.param("gain")
        spec.input("signal_in")
        spec.output("signal_out")

    def initialize(self):
        Operator.initialize(self)
        self.up, self.down = None, None
        self.sample_rate_in = None
        self.sample_rate_out = float(self.sample_rate_out)

    def _set_scaling(self):
        fs_small = min(self.sample_rate_in, self.sample_rate_out)
        fs_large = max(self.sample_rate_in, self.sample_rate_out)
        self.up, self.down = reduce_fraction(fs_large, fs_small)

    def _resample(self, data):
        if self.up == self.down:
            return data
        return cusignal.resample_poly(
            data, self.up, self.down, window="hamming"
        ).astype(cp.float32)

    def compute(self, op_input, op_output, context):
        signal_in = op_input.receive("signal_in")

        # Check if up/down conversion needs to be re-computed
        if self.sample_rate_in != signal_in.fs:
            self.sample_rate_in = signal_in.fs
            self._set_scaling()

        # Do work and emit
        data = self.gain * self._resample(signal_in.data)
        signal_out = SignalEmission(data, self.sample_rate_out)
        op_output.emit(signal_out, "signal_out")


class PcmToAsrOp(Operator):
    """
    Converts signal from float to PCM16 format, and moves it to host for processing by Riva.
    A seperate running thread that is reading the same shared buffer picks up the data and
    sends to Riva.
    """
    def __init__(self, fragment, shared_pcm_buffer, *args, **kwargs):
        super().__init__(fragment, *args, **kwargs)
        self.logger = setup_logging(self.name)
        self.shared_pcm_buffer = shared_pcm_buffer

    def setup(self, spec: OperatorSpec):
        spec.input("signal_in")

    def compute(self, op_input, op_output, context):
        signal_in = op_input.receive("signal_in")

        # Put 16-bit PCM byte array on shared Riva buffer
        pcm_data = float_to_pcm(signal_in.data, cp.int16)
        byte_array = cp.asnumpy(pcm_data).tobytes()
        self.shared_pcm_buffer.put(
            rasr.StreamingRecognizeRequest(audio_content=byte_array)
        )
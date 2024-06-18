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
Given a .wav audio file, this function will convert the floating-point
audio samples to I/Q FM-modulated samples and send them as UDP packets
downstream to the Holoscan SDR application. Note that the replay parameters
used here should match up with the expected parameters in the SDR's
params.yml file.
"""

import time
import os
import logging
import librosa
import argparse
import struct
import socket

import cupy as cp
import cupyx.scipy.signal as cusignal

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay audio file as UDP packets with I/Q samples"
    )
    parser.add_argument(
        "--dst-ip",
        type=str,
        default="0.0.0.0",
        help="IP address, should match 'network_rx.ip_addr' in sdr-holoscan/params.yml"
    )
    parser.add_argument(
        "--dst-port",
        type=int,
        default=5005,
        help="Destination port, should match 'network_rx.dst_port' in sdr-holoscan/params.yml"
    )
    parser.add_argument(
        "--file-name",
        type=str,
        nargs="?",
        const="",
        default="",
        help="Filename, should be located in file-replay/files"
    )
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=1e6,
        help="Output sample rate, should match 'sensor.sample_rate' in sdr-holoscan/params.yml"
    )
    parser.add_argument(
        "--packet-size",
        type=int,
        default=1472,
        help="Size in bytes of each UDP packet, plus 8 counting bytes at front"
    )
    parser.add_argument(
        "--init-time",
        type=float,
        default=30,
        help="Sleep time prior to starting, allows other containers to spin up."
    )
    parser.add_argument(
        "--total-time",
        type=float,
        default=0,
        help="Total runtime. If non-zero, loops until time is hit if .wav file is shorter."
    )
    return parser.parse_args()

def wait_for_dst(dst_ip, dst_port, wait_time=5, timeout=300):
    """ Try to connect until successful
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((dst_ip, dst_port))
    start_time = time.time()
    curr_time = start_time
    while curr_time - start_time < timeout:
        try:
            sock.sendto(struct.pack('Q', 0), (dst_ip, dst_port))
            logger.info(f"{dst_ip}:{dst_port} open, replaying")
            return
        except ConnectionRefusedError:
            logger.info(f"Waiting {wait_time}s for {dst_ip}:{dst_port} to open")
            time.sleep(wait_time)
    logger.error(f"{dst_ip}:{dst_port} never opened")

def fm_modulate(audio, fs_in, fs_out, deviation=100000):
    """ Given audio samples in floating point"""
    # Resample
    nsamples = int(audio.shape[0] * fs_out / fs_in)
    chunk = cusignal.resample(audio, nsamples)

    # Integrate and frequency modulate
    integrated_audio = cp.cumsum(chunk) / fs_out
    phase_deviation = 2 * cp.pi * deviation * integrated_audio
    samples = cp.cos(phase_deviation) + 1j*cp.sin(phase_deviation)
    return samples.astype(cp.complex64)

def send_packet(sock, data, dst_ip, dst_port):
    try:
        sock.sendto(data, (dst_ip, dst_port))
        return None
    except Exception as e:
        return e

def replay(file_name, fs_out, dst_ip, dst_port, pkt_size, chunk_time=2, total_time=0):
    file_path = os.path.join("files", file_name)
    fs_in = librosa.get_samplerate(file_path)

    # Setup socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((dst_ip, dst_port))

    # Warm start
    audio, _ = librosa.load(file_path, duration=chunk_time)
    samples = fm_modulate(cp.array(audio), fs_in, fs_out)
    iq_data = samples.tobytes()

    if not total_time:
        total_time = librosa.get_duration(path=file_path)

    # Stream in file
    elapsed = 0
    while elapsed < total_time:
        stream = librosa.stream(
            file_path,
            block_length=1,
            frame_length=chunk_time * fs_in,
            hop_length=chunk_time * fs_in
        )
        for audio in stream:
            # Reset stats
            start_time = time.time()
            prev_time = start_time
            pkts_sent = 0
            bytes_sent = 0

            # Convert WAV to I/Q samples
            samples = fm_modulate(cp.array(audio), fs_in, fs_out)
            iq_data = samples.tobytes()
            inter_pkt_time = chunk_time / (len(iq_data) // pkt_size)

            # Form packet and send
            for i in range(0, len(iq_data), pkt_size):
                # Send
                header = struct.pack('Q', pkts_sent)
                pkt_data = iq_data[i:i+pkt_size]
                result = send_packet(sock, header + pkt_data, dst_ip, dst_port)
                while result is ConnectionRefusedError:
                    logger.info(f"Connection refused, sleeping 5s")
                    time.sleep(5)
                    result = send_packet(sock, header + pkt_data, dst_ip, dst_port)

                pkts_sent += 1
                bytes_sent += len(pkt_data)

                # Wait allotted time
                curr_time = time.time()
                while (curr_time - prev_time) < inter_pkt_time:
                    curr_time = time.time()
                prev_time = curr_time

            # Print stats
            dt = curr_time - start_time
            elapsed += dt
            logger.info(f"Stats ({elapsed:.2f}s):")
            logger.info(f" - {pkts_sent} packets")
            logger.info(f" - {bytes_sent} bytes")
            logger.info(f" - {bytes_sent / dt / 1e6:.2f} MB/s")

            if elapsed >= total_time:
                break

if __name__ == "__main__":
    args = parse_args()
    if not args.file_name:
        logger.info("No file provided, exiting")
        exit()
    elif args.file_name.split('.')[-1].lower() != "wav":
        logger.error(f"Only configured for .wav, cannot play {args.file_name}")
        raise ValueError

    # Wait for other apps
    logger.info(f"Sleeping {args.init_time}s to allow time for SDR to spin up")
    time.sleep(args.init_time)
    wait_for_dst(args.dst_ip, args.dst_port)

    # Do replay
    replay(
        args.file_name,
        args.sample_rate,
        args.dst_ip,
        args.dst_port,
        args.packet_size,
        total_time=args.total_time
    )
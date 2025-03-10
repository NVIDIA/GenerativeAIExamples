/* 

SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

*/

import React, { useEffect, useRef, useState } from "react";
import { MdMic, MdStop } from "react-icons/md";
import { io } from "socket.io-client";

const MicButton = ({
  onTranscription,
  updatePlaceholder,
  messageSent,
  setMessageSent,
  disabled,
}) => {
  const [isListening, setIsListening] = useState(false);
  const audioContextRef = useRef(null);
  const workerRef = useRef(null);
  const localStreamRef = useRef(null);
  const socketRef = useRef(null);
  const processorRef = useRef(null);

  const initializeAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      localStreamRef.current = stream;
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      socketRef.current = io(process.env.REACT_APP_SERVER_URL, {
          secure: true,
          rejectUnauthorized: false,
      });
      socketRef.current.on('connect', () => {
        console.log('Connected to speech server');
      });
      socketRef.current.on('transcript', (result) => {
        if (result.transcript) {
          onTranscription(result.transcript, result.is_final);
          updatePlaceholder(!result.is_final);
        }
      });

    } catch (err) {
      console.error("Microphone access error:", err);
      alert("Microphone access required for voice input");
    }
  };

  const startListening = async () => {
    if (!localStreamRef.current) {
      await initializeAudio();
    }

    if (!socketRef.current.connected) {
      socketRef.current.connect();
    }

    const audioInput = audioContextRef.current.createMediaStreamSource(localStreamRef.current);
    const bufferSize = 4096;
    processorRef.current = audioContextRef.current.createScriptProcessor(bufferSize, 1, 1);

    workerRef.current = new Worker('./resampler.js');
    workerRef.current.postMessage({
      command: 'init',
      config: {
        sampleRate: audioContextRef.current.sampleRate,
        outputSampleRate: 16000
      }
    });

    processorRef.current.onaudioprocess = (event) => {
      const inputBuffer = event.inputBuffer;
      workerRef.current.postMessage({
        command: 'convert',
        buffer: inputBuffer.getChannelData(0)
      });
    };

    workerRef.current.onmessage = (msg) => {
      if (msg.data.command === 'newBuffer') {
        socketRef.current.emit('audio_in', msg.data.resampled.buffer);
      }
    };

    audioInput.connect(processorRef.current);
    processorRef.current.connect(audioContextRef.current.destination);
    setIsListening(true);
    updatePlaceholder(true);
  };

  const stopListening = () => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      workerRef.current?.terminate();
      localStreamRef.current?.getTracks().forEach(track => track.stop());
      localStreamRef.current = null;
      socketRef.current?.disconnect();
      setIsListening(false);
      updatePlaceholder(false);
    }
  };

  useEffect(() => {
    if (messageSent) {
      stopListening();
      setMessageSent(false);
    }
  }, [messageSent, setMessageSent]);

  const toggleListening = () => {
    isListening ? stopListening() : startListening();
  };

  return (
    <button
      onClick={toggleListening}
      className={`absolute right-11 bottom-1.5 h-8 w-8 rounded-full p-1 flex items-center justify-center ${
        disabled
          ? "bg-gray-400 cursor-not-allowed"
          : isListening
          ? "bg-red-500 animate-pulse hover:opacity-80 hover:cursor-pointer"
          : "bg-green-500 hover:opacity-80 hover:cursor-pointer"
      } text-white`}
      disabled={disabled}
    >
      {isListening ? <MdStop size="1.2em" /> : <MdMic size="1.2em" />}
    </button>
  );
};

export default MicButton;

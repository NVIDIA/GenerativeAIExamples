/**
 * Copyright 2020 NVIDIA Corporation. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

require('dotenv').config({path: 'env.txt'});

const defaultRate = 16000;
const languageCode = 'en-US';

// Because of a quirk in proto-loader, we use static code gen to get the AudioEncoding enum,
// and dynamic loading for the rest.
const rAudio = require('./protos/src/riva_proto/riva_audio_pb');

const { Transform } = require('stream');

var asrProto = 'src/riva_proto/riva_asr.proto';
var protoRoot = __dirname + '/protos/';
var grpc = require('grpc');
var protoLoader = require('@grpc/proto-loader');
const { request } = require('express');
var protoOptions = {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true,
    includeDirs: [protoRoot]
};
var asrPkgDef = protoLoader.loadSync(asrProto, protoOptions);
var rAsr = grpc.loadPackageDefinition(asrPkgDef).nvidia.riva.asr;

console.log(rAudio.AudioEncoding);

class ASRPipe {
    setupASR() {
        // the Riva ASR client
        this.asrClient = new rAsr.RivaSpeechRecognition(process.env.RIVA_API_URL, grpc.credentials.createInsecure());
        this.firstRequest = {
            streaming_config: {
                config: {
                    encoding: rAudio.AudioEncoding.LINEAR_PCM,
                    sample_rate_hertz: defaultRate,
                    language_code: languageCode,
                    max_alternatives: 1,
                    enable_automatic_punctuation: true
                },
                interim_results: true
            }
        };
        this.numCharsPrinted = 0;
    }

    async mainASR(transcription_cb) {
        this.recognizeStream = this.asrClient.streamingRecognize()
        .on('data', function(data){
            if (data.results == undefined) {
                return;
            }

            let partialTranscript = '';

            // callback sends the transcription results back through the bidirectional socket stream
            data.results.forEach(function(result, i) {
                if (result.alternatives == undefined) {
                    return;
                }

                let transcript = result.alternatives[0].transcript;
                if (!result.is_final) {
                    partialTranscript += transcript;
                } else {
                    transcription_cb({
                        transcript: transcript,
                        is_final: result.is_final
                    });
                }
            });
            
            if (partialTranscript != '') {
                transcription_cb({
                    transcript: partialTranscript,
                    is_final: false
                });
            }
        })
        .on('error', (error) => {
            console.log('Error via streamingRecognize callback');
            console.log(error);
        })
        .on('end', () => {
            console.log('StreamingRecognize end');
        });
    
        this.recognizeStream.write(this.firstRequest);
    }
}

module.exports = ASRPipe;
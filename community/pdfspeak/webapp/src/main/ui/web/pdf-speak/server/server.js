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

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0"; // Insecure: Use only for debugging
require('dotenv').config({path: './server/env.txt'});

const socketIo = require('socket.io');
const path = require('path');
const fs = require('fs');
const https = require('https');
const cors = require('cors');
const express = require('express');
const session = require('express-session')({
    secret: "gVkYp3s6",
    resave: true,
    saveUninitialized: true,
    genid: function(req) {
        return uuid.v4();
    }
});
const uuid = require('uuid');
const sharedsession = require("express-socket.io-session");

const ASRPipe = require('./modules/asr');

const app = express();
const port = ( process.env.PORT );
var server;
// var sslkey = '../.certs/localhost.key';
// var sslcert = '../.certs/localhost.crt';
var sslkey = '.certs/localhost.key';
var sslcert = '.certs/localhost.crt';

/**
 * Set up Express Server with CORS and SocketIO
 */
function setupServer() {
    // set up Express
    const corsOptions = {
        origin: "*",
        methods: ["GET", "POST"],
        credentials: true, 
    };
    app.use(cors(corsOptions));
    app.use(express.static('web')); // ./web is the public dir for js, css, etc.
    app.use(session);
    app.get('/', function(req, res) {
         res.sendFile('./web/index.html', { root: __dirname });
    });
    server = https.createServer({
        key: fs.readFileSync(sslkey),
        cert: fs.readFileSync(sslcert),
        requestCert: false,
        rejectUnauthorized: false
    }, app);

    io = socketIo(server, {cors: corsOptions, secure: true});
    io.use(sharedsession(session, {autoSave:true}));
    server.listen(port, () => {
        console.log('Running server on port %s', port);
    });

    console.log("process.env.process.env.PORT", process.env.PORT);
    console.log("process.env.NODE_TLS_REJECT_UNAUTHORIZED", process.env.NODE_TLS_REJECT_UNAUTHORIZED);
    // Listener, once the client connects to the server socket
    io.on('connect', (socket) => {
        console.log('Client connected from %s', socket.handshake.address);

        // Initialize Riva
        console.log('Initializing Riva ASR');
        socket.handshake.session.asr = new ASRPipe();
        socket.handshake.session.asr.setupASR();
        socket.handshake.session.asr.mainASR(function(result){
            if (result.transcript == undefined) {
                return;
            }
            // Log the transcript to console, overwriting non-final results
            process.stdout.write(''.padEnd(process.stdout.columns, ' ') + '\r')
            if (!result.is_final) {
                process.stdout.write('TRANSCRIPT: ' + result.transcript + '\r');
            } else {
                process.stdout.write('TRANSCRIPT: ' + result.transcript + '\n');
            }
            socket.handshake.session.lastLineLength = result.transcript.length;

            // Final transcripts also get sent to NLP before returning

            socket.emit('transcript', result);
        });

        // incoming audio
        socket.on('audio_in', (data) => {
            socket.handshake.session.asr.recognizeStream.write({audio_content: data});
        });

        socket.on('disconnect', (reason) => {
            console.log('Client at %s disconnected. Reason: ', socket.handshake.address, reason);
        });
    });
};

setupServer();
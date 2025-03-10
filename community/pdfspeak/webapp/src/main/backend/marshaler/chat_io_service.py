# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import PyPDF2
import os

# Comment for dev / Uncomment for Docker
from marshaler.nim_client import request_nvidia_llama
from marshaler.pdf_processor import pdf_highlighter
from marshaler.riva_connector import generate_tts
from marshaler.nv_ingest_helper import ingestor, rag_chain

# Uncomment for dev / Comment for Docker
# from nim_client import request_nvidia_llama
# from pdf_processor import pdf_highlighter
# from riva_connector import generate_tts
# from nv_ingest_helper import ingestor, rag_chain

app = Flask(__name__)
CORS(app)

@app.route("/v1/chat/simple", methods=["POST"])
def process_message_simple_test():
    data = request.json
    messages = data.get("messages", [])
    pdf_context = data.get("pdfContext", "")
    response = request_nvidia_llama(messages, pdf_context)
    generate_tts(response)
    pdf_highlighter(response, 'uploads/' + pdf_context['filename'])
    return response

# NV Ingest Workflow API

@app.route("/v1/chat/nvingest", methods=["POST"])
def process_message_nvingest():
    data = request.json
    messages = data.get("messages", [])
    last_user_message = messages[-1]["content"]
    print("[INFO] In NV Ingest with message", last_user_message)
    response = rag_chain(last_user_message)
    print("Response Received from NVINgest: ", response)
    generate_tts(response)
    pdf_highlighter(response, 'uploads/' + data.get("pdfContext")['filename'])
    return response


@app.route('/v1/api/upload_pdf', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.pdf'):
        pdf_path = f"uploads/{file.filename}"
        file.save(pdf_path)

        # Logic below for extracting text. To be replaced with NVIngest workflow
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        # NVIngest PDF Ingestion API call to be added below. 
        print("[INFO] Ingestion Begins", flush=True)
        ingestor(pdf_path)
        print("[INFO] Ingestion Complete", flush=True)

        return jsonify({
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "text": text,
            "pdf_path": pdf_path 
        })
    
    return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

@app.route('/v1/api/download_pdf', methods=['GET'])
def download_pdf():
    pdf_filename = request.args.get('filename')
    return send_file('../uploads/'+pdf_filename, as_attachment=True)

@app.route('/v1/api/download_audio', methods=['GET'])
def download_audio():
    audio_filename = request.args.get('filename')
    return send_file(f'../audio_outputs/{audio_filename}', mimetype='audio/wav')

@app.route("/v1/api/generate_welcome_audio", methods=["POST"])
def generate_welcome_audio():
    print("[INFO] Inside Generate Welcome Audio", flush=True)
    welcome_text = request.json.get('text', '')
    audio_path = generate_tts(welcome_text, "assistant_output.wav")
    print("[INFO] Received Welcome Audio", flush=True)
    return jsonify({"status": "success", "audio_path": audio_path})


if __name__ == '__main__':
    print(os.getcwd())
    print(os.listdir())
    app.run(host="0.0.0.0", debug=True)

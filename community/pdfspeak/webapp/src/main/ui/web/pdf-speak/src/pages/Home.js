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

import React, {useEffect, useRef, useState} from 'react';
import {Helmet} from 'react-helmet';
import Chat from '../components/Chat/Chat';
import Footer from '../components/Layout/Footer';
import Navbar from '../components/Layout/Navbar';
import SidePanel from '../components/Layout/SidePanel';
import {API_BASE_URL, API_ENDPOINTS, WELCOME_TEXT} from './APIConfig';
import logo from '../store/nvidia-logo-vert-rgb-blk-for-screen.png'

const Home = () => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [pdfContext, setpdfContext] = useState('');
    const [uploadedFile, setUploadedFile] = useState(null);
    const [pdfUrl, setPdfUrl] = useState(null);
    const messagesEndRef = useRef(null);
    const [isExpanded, setIsExpanded] = useState(false);
    const audioRef = useRef(new Audio());

    const generateWelcomeAudio = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.GENERATE_WELCOME_AUDIO}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: WELCOME_TEXT
                })
            });
            if (!response.ok) throw new Error('Welcome audio generation failed');
        } catch (error) {
            console.error("Error generating welcome audio:", error);
        }
    };

    const playAssistantAudio = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.ASSISTANT_RESPONSE_AUDIO_DOWNLOAD}?filename=assistant_output.wav`);
            if (!response.ok) throw new Error('Audio fetch failed');
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            audioRef.current.src = audioUrl;
            await audioRef.current.play();
            
            audioRef.current.onended = () => URL.revokeObjectURL(audioUrl);
        } catch (error) {
            console.error("Error playing audio:", error);
        }
    };
    const getApiEndpoint = () => {
            // return API_ENDPOINTS.SIMPLE_CHAT;
            return API_ENDPOINTS.NV_INGEST_CHAT;
    };

    const scrollToBottom = () => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({behavior: "smooth"});
        }
    };

    const handleSend = async (message) => {
        const updatedMessages = [...messages, message];
        setMessages(updatedMessages);
        setLoading(true);

        try {
            const endpoint = getApiEndpoint();
            const bodyPayload = {
                messages: updatedMessages,
                pdfContext: pdfContext,
                pdf_filename: uploadedFile ? uploadedFile.name : null
            };
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(bodyPayload)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = response.body;
            if (!data) {
                return;
            }

            const reader = data.getReader();
            const decoder = new TextDecoder();
            let done = false;
            let isFirst = true;

            while (!done) {
                const {value, done: doneReading} = await reader.read();
                done = doneReading;
                const chunkValue = decoder.decode(value);

                if (isFirst) {
                    isFirst = false;
                    setMessages((messages) => [
                        ...messages,
                        {
                            role: "assistant",
                            content: chunkValue
                        }
                    ]);
                } else {
                    setMessages((messages) => {
                        const lastMessage = messages[messages.length - 1];
                        const updatedMessage = {
                            ...lastMessage,
                            content: lastMessage.content + chunkValue
                        };
                        return [...messages.slice(0, -1), updatedMessage];
                    });
                }
            }

            playAssistantAudio();

            setMessages((messages) => [
                ...messages,
                {
                    role: "assistant",
                    content: `Download Highlighted References: [${pdfContext['filename'].slice(0, -4)}](${API_BASE_URL}${API_ENDPOINTS.PDF_DOWNLOAD}?filename=${encodeURIComponent(pdfContext['filename'].slice(0, -4))}_highlighted.pdf)`
                }
            ]);  
            
            if (pdfContext && pdfContext.filename) {
                const pdfResponse = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PDF_DOWNLOAD}?filename=${encodeURIComponent(pdfContext.filename.slice(0, -4))}_highlighted.pdf`);
                if (pdfResponse.ok) {
                    const pdfBlob = await pdfResponse.blob();
                    setPdfUrl(URL.createObjectURL(pdfBlob));
                }
            }
            
        } catch (error) {
            console.error("Error in sending message:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleReset = async () => {
        await generateWelcomeAudio();
        setMessages([
            {
                role: "assistant",
                content: WELCOME_TEXT
            }
        ]);
        await playAssistantAudio();
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        const initializeApp = async () => { 
            await generateWelcomeAudio();
            setMessages([
            {
                role: "assistant",
                content: `Hey there! Welcome to PDFSpeak. Upload your document of interest and talk to it in real-time! Be it a simple summary or a complex analysis, PDFSpeak has got you covered. Ask away!!`
            }
        ]);

        await playAssistantAudio();
    };
    initializeApp();
    }, []);

    useEffect(() => {
        return () => {
            audioRef.current.pause();
            audioRef.current.src = '';
        };
    }, []);

    return (
        <>
            <Helmet>
                <title>PDFSpeak - Talk to Your PDF</title>
                <link rel="icon" href={logo} type="image/png"/>
            </Helmet>
            <div className="flex flex-col h-screen">
                <Navbar/>
    
                <div className="flex-1 flex overflow-hidden">
                    <div className={`flex-1 overflow-auto transition-all duration-300 ${
                        isExpanded ? 'sm:px-4' : 'sm:px-10'
                    }`}>
                        <div className={`mx-auto mt-4 sm:mt-12 pb-8 ${
                            isExpanded ? 'max-w-[775px]' : 'max-w-[800px]'
                        }`}>
                            <Chat
                                messages={messages}
                                loading={loading}
                                onSend={handleSend}
                                onReset={handleReset}
                                setpdfContext={setpdfContext}
                                uploadedFile={uploadedFile}
                                setUploadedFile={setUploadedFile}
                                audioRef={audioRef}
                            />
                            <div ref={messagesEndRef}/>
                        </div>
                    </div>
                        <SidePanel pdfUrl={pdfUrl} isExpanded={isExpanded} setIsExpanded={setIsExpanded} /> 
                </div>
    
                <Footer/>
            </div>
        </>
    );    
};

export default Home;

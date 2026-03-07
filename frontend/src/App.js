// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Copyright (c) 2023-2025, NVIDIA CORPORATION.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ProjectKnowledge from './pages/ProjectKnowledge';
import configLoader from './config/config_loader';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [detailedThinking, setDetailedThinking] = useState(false);
  const [conversationSummary, setConversationSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [usePictures, setUsePictures] = useState(true);
  const [expandedRefs, setExpandedRefs] = useState({});
  const [appConfig, setAppConfig] = useState(null);
  const [pictureSearchQuery, setPictureSearchQuery] = useState('');
  const [pictureSearchResults, setPictureSearchResults] = useState([]);
  const [pictureSearchLoading, setPictureSearchLoading] = useState(false);
  const [pictureSearchError, setPictureSearchError] = useState('');
  const [pinnedPicture, setPinnedPicture] = useState(null);
  const [pictureSidecarOpen, setPictureSidecarOpen] = useState(true);
  const [pictureSidecarAutoCollapsed, setPictureSidecarAutoCollapsed] = useState(false);

  // NEW: view toggle for Option C
  const [view, setView] = useState("chat"); // "chat" | "knowledge"

  const [serverIp, setServerIp] = useState(() => {
    // Load IP from localStorage on initial render
    const savedIp = localStorage.getItem('serverIp') || '';
    return savedIp;
  });
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const errorTimeoutRef = useRef(null);

  useEffect(() => {
    // Load configuration
    const loadConfig = async () => {
      try {
        const loadedConfig = await configLoader.getAppConfig();
        
        if (!loadedConfig) {
          return;
        }
        
        setAppConfig(loadedConfig);
      } catch (error) {
        // Silent error handling for production
      }
    };
    loadConfig();
  }, []);

  // Save IP to localStorage and configLoader whenever it changes
  useEffect(() => {
    if (serverIp) {
      localStorage.setItem('serverIp', serverIp);
      configLoader.serverIp = serverIp;
    } else {
      localStorage.removeItem('serverIp');
      configLoader.serverIp = '';
    }
  }, [serverIp]);

  useEffect(() => {
    if (!serverIp) {
      const fallbackHost = window.location.hostname || '127.0.0.1';
      if (fallbackHost) {
        setServerIp(fallbackHost);
      }
    }
  }, [serverIp]);

  // Auto-dismiss error after 5 seconds
  useEffect(() => {
    if (error) {
      // Clear any existing timeout
      if (errorTimeoutRef.current) {
        clearTimeout(errorTimeoutRef.current);
      }
      
      // Set new timeout
      errorTimeoutRef.current = setTimeout(() => {
        const errorElement = document.querySelector('.error-message');
        if (errorElement) {
          errorElement.classList.add('fade-out');
          // Remove the error after animation completes
          setTimeout(() => {
            setError(null);
            errorTimeoutRef.current = null;
          }, 300); // Match the animation duration
        }
      }, 5000);
    }
    
    return () => {
      if (errorTimeoutRef.current) {
        clearTimeout(errorTimeoutRef.current);
      }
    };
  }, [error]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  useEffect(() => {
    if (pictureSearchResults.length > 0 && !pictureSidecarAutoCollapsed) {
      setPictureSidecarOpen(false);
      setPictureSidecarAutoCollapsed(true);
    }
  }, [pictureSearchResults, pictureSidecarAutoCollapsed]);

  const updateSummary = async (messages) => {
    try {
      const maxMessages = appConfig?.ui?.chat?.summary?.max_messages || 5;
      const summaryMessages = messages.slice(-maxMessages).filter(msg => 
        msg.role === 'user' || msg.role === 'assistant'
      );

      const response = await fetch(`${configLoader.api.llmServer.url}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          ...configLoader.api.llmServer.headers,
          ...(appConfig?.llm?.base_url?.includes(":8002")
            ? { 'X-LLM-IP': serverIp }
            : {})
        },
        body: JSON.stringify({
          model: appConfig?.llm?.model?.name || "nvidia/Llama-3.1-Nemotron-Nano-4B-v1.1",
          messages: [
            {
              role: "system",
              content: appConfig?.ui?.chat?.summary?.system_prompt || "Provide a brief summary of the key points from this conversation. Focus on the main topics and decisions made."
            },
            ...summaryMessages
          ],
          stream: false,
          max_tokens: appConfig?.llm?.model?.max_tokens || 512
        }),
      });

      if (response.ok) {
        const data = await response.json();
        return data.choices[0].message.content;
      }
      return "Unable to generate summary";
    } catch (error) {
      return `Error generating summary: ${error.message}`;
    }
  };

  const searchRAG = async (query) => {
    if (!useRag) return [];
    
    try {
      if (!appConfig) {
        return [];
      }
      
      console.log('Performing RAG search for query:', query);
      
      const response = await fetch(`${appConfig.api.base_url}${appConfig.api.endpoints.search}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query,
          use_rag: true,
          k: appConfig?.ui?.components?.search?.default_k || 5
        }),
      });

      if (!response.ok) {
        console.error('RAG search failed:', await response.text());
        throw new Error('RAG search failed');
      }

      const data = await response.json();
      console.log('Raw RAG search results:', data);
      
      // Log detailed information about each result
      if (data.results && data.results.length > 0) {
        console.log('RAG Results Analysis:');
        data.results.forEach((result, index) => {
          console.log(`\nResult ${index + 1}:`);
          console.log(`- Score: ${result.score}`);
          console.log(`- Source: ${result.source_file}`);
          console.log(`- Text Preview: ${result.text.substring(0, 100)}...`);
        });
      } else {
        console.log('No RAG results found');
      }
      
      return data.results || [];
    } catch (error) {
      console.error('RAG search error:', error);
      return [];
    }
  };

  const prepareContextMessages = (messages, detailedThinking, conversationSummary, ragResults) => {
    const contextMessages = [];
    
    // Add system message with safe fallback
    const systemPrompt = appConfig?.ui?.chat?.context?.system_prompt || 'detailed thinking {status}.';
    contextMessages.push({
      role: "system",
      content: systemPrompt.replace('{status}', detailedThinking ? 'on' : 'off')
    });
    
    // Add conversation summary if exists and is not empty
    if (conversationSummary && conversationSummary.trim() !== '') {
      contextMessages.push({
        role: "user",
        content: `Previous conversation summary: ${conversationSummary}`
      });
    }
    
    // Process messages in pairs to ensure proper alternation
    let i = 0;
    while (i < messages.length) {
      if (i < messages.length && messages[i].role === 'user') {
        contextMessages.push({
          role: messages[i].role,
          content: messages[i].content
        });
        i++;
        if (i < messages.length && messages[i].role === 'assistant') {
          contextMessages.push({
            role: messages[i].role,
            content: messages[i].content
          });
          i++;
        }
      } else {
        i++;
      }
    }
    
    return contextMessages;
  };


  const norm = (s) => String(s || "").replace(/\s+/g, " ").trim();
  const normLower = (s) => norm(s).toLowerCase();

  const getPageNo = (obj) => {
    const prov = Array.isArray(obj?.prov) ? obj.prov : [];
    const pageNo = prov[0]?.page_no;
    return Number.isInteger(pageNo) ? pageNo : null;
  };

  const getItemBbox = (obj) => {
    const prov = Array.isArray(obj?.prov) ? obj.prov : [];
    const bbox = prov[0]?.bbox;
    return bbox && typeof bbox === "object" ? bbox : null;
  };

  const getTextByRefMap = (doc) => {
    const map = new Map();
    const texts = Array.isArray(doc?.texts) ? doc.texts : [];
    for (const t of texts) {
      if (t?.self_ref) {
        map.set(t.self_ref, norm(t?.text || t?.orig || ""));
      }
    }
    return map;
  };

  const getPictureCaption = (doc, picture) => {
    const textByRef = getTextByRefMap(doc);
    const captions = Array.isArray(picture?.captions) ? picture.captions : [];
    const captionTexts = captions
      .map((c) => (c && typeof c === "object" ? c.$ref : null))
      .filter(Boolean)
      .map((ref) => textByRef.get(ref))
      .filter((t) => norm(t));
    if (captionTexts.length) return captionTexts.join("\n\n");

    const ann = Array.isArray(picture?.annotations) ? picture.annotations : [];
    for (const a of ann) {
      if (a?.kind === "description" && norm(a?.text)) return norm(a.text);
    }

    const meta = picture?.meta && typeof picture.meta === "object" ? picture.meta : {};
    return norm(meta.description || meta.caption || meta.desc || "");
  };

  const getPageObject = (doc, pageNo) => {
    const pages = doc?.pages;
    if (!pages || typeof pages !== "object") return null;
    return pages[String(pageNo)] || pages[pageNo] || null;
  };

  const cropPictureFromPage = async (doc, pageNo, bbox, padPx = 2) => {
    try {
      if (!Number.isInteger(pageNo) || !bbox || typeof bbox !== "object") return null;
      const page = getPageObject(doc, pageNo);
      if (!page || typeof page !== "object") return null;
      const imgMeta = page.image;
      let src = null;
      let pxW = 0;
      let pxH = 0;

      if (imgMeta && typeof imgMeta === "object") {
        if (typeof imgMeta.uri === "string" && imgMeta.uri) src = imgMeta.uri;
        if (imgMeta.size && typeof imgMeta.size === "object") {
          pxW = Number(imgMeta.size.width || 0);
          pxH = Number(imgMeta.size.height || 0);
        }
      } else if (typeof imgMeta === "string") {
        src = imgMeta;
      }

      if (!src || !pxW || !pxH) return null;

      const left = Math.max(0, Math.floor(Math.min(bbox.l, bbox.r) - padPx));
      const top = Math.max(0, Math.floor(Math.min(bbox.t, bbox.b) - padPx));
      const width = Math.max(1, Math.floor(Math.abs(bbox.r - bbox.l) + padPx * 2));
      const height = Math.max(1, Math.floor(Math.abs(bbox.b - bbox.t) + padPx * 2));

      return await new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          try {
            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, left, top, width, height, 0, 0, width, height);
            resolve(canvas.toDataURL("image/png"));
          } catch (_) {
            resolve(null);
          }
        };
        img.onerror = () => resolve(null);
        img.src = src;
      });
    } catch (_) {
      return null;
    }
  };

  const fetchDoc = async (sourceFile) => {
    const baseUrl = appConfig?.api?.base_url || "http://localhost:8001";
    const resp = await fetch(`${baseUrl}/api/document/${encodeURIComponent(sourceFile)}`, {
      headers: { Accept: "application/json" },
    });
    if (!resp.ok) return null;
    return await resp.json();
  };

  const extractMatchingPicturesFromDoc = async (doc, sourceFile, needle, score = null) => {
    const out = [];
    const pictures = Array.isArray(doc?.pictures) ? doc.pictures : [];
    const n = normLower(needle);
    for (let i = 0; i < pictures.length; i++) {
      const picture = pictures[i];
      if (!picture || typeof picture !== "object") continue;
      const caption = getPictureCaption(doc, picture);
      const matchText = caption || "picture";
      if (n && !normLower(matchText).includes(n)) continue;
      const pageNo = getPageNo(picture);
      const bbox = getItemBbox(picture);
      const imageDataUrl = await cropPictureFromPage(doc, pageNo, bbox);
      out.push({
        kind: "picture",
        title: caption || doc?.name || `picture ${i + 1}`,
        body: caption || "(no caption)",
        imageDataUrl,
        page_no: pageNo,
        source_file: sourceFile,
        doc_name: doc?.name || "",
        score,
      });
    }
    return out;
  };

  const buildPictureResultsFromSearch = async (query, refs) => {
    const out = [];
    const seen = new Set();
    const relevanceThreshold = appConfig?.ui?.components?.search?.relevance_threshold || 0.3;
    const filteredRefs = (refs || []).filter((ref) => (ref?.score || 0) > relevanceThreshold).slice(0, 8);

    for (const ref of filteredRefs) {
      const sourceFile = String(ref?.source_file || '').trim();
      if (!sourceFile) continue;
      const doc = await fetchDoc(sourceFile);
      if (!doc) continue;

      let pictures = await extractMatchingPicturesFromDoc(doc, sourceFile, query, ref.score);
      if (!pictures.length) {
        pictures = (await extractMatchingPicturesFromDoc(doc, sourceFile, '', ref.score)).slice(0, 1);
      }

      for (const picture of pictures) {
        const key = `${picture.source_file || ''}::${picture.page_no || ''}::${picture.title || ''}`;
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(picture);
        if (out.length >= 12) return out;
      }
    }

    return out;
  };

  const searchChunks = async (query, options = {}) => {
    if (!appConfig) return [];

    const cleanQuery = String(query || '').trim();
    if (!cleanQuery) return [];

    const k = Number.isInteger(options.k) ? options.k : (appConfig?.ui?.components?.search?.default_k || 5);
    const baseUrl = appConfig?.api?.base_url || 'http://localhost:8001';
    const searchEndpoint = appConfig?.api?.endpoints?.search || '/api/search';

    const response = await fetch(`${baseUrl}${searchEndpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: cleanQuery,
        use_rag: true,
        k,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chunk search failed: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return Array.isArray(data?.results) ? data.results : [];
  };

  const runPictureContextSearch = async (query) => {
    const cleanQuery = String(query || '').trim();
    if (!cleanQuery) return;

    setPictureSearchQuery(cleanQuery);
    setPictureSearchLoading(true);
    setPictureSearchError('');

    try {
      const refs = await searchChunks(cleanQuery, { k: 8 });
      const pictures = await buildPictureResultsFromSearch(cleanQuery, refs);
      setPictureSearchResults(pictures);
      if (!pictures.length) {
        setPictureSearchError('No matching pictures found for this query.');
      }
    } catch (error) {
      console.error('Picture context search failed:', error);
      setPictureSearchResults([]);
      setPictureSearchError('Picture search failed.');
    } finally {
      setPictureSearchLoading(false);
    }
  };

  const pinPictureToChat = (picture) => {
    setPinnedPicture(picture || null);
  };

  const [referenceExtras, setReferenceExtras] = useState({});

  useEffect(() => {
    let cancelled = false;

    const loadReferenceExtras = async () => {
      if (!usePictures || !appConfig) return;

      const nextExtras = {};

      for (const msg of messages) {
        if (msg.role !== "assistant" || !msg.references) continue;

        let refs = [];
        try {
          refs = JSON.parse(msg.references);
        } catch (_) {
          refs = [];
        }

        const relevanceThreshold = appConfig?.ui?.components?.search?.relevance_threshold || 0.3;
        const filteredRefs = refs.filter((ref) => ref.score > relevanceThreshold).slice(0, 5);

        for (const ref of filteredRefs) {
          const sourceFile = String(ref?.source_file || "").trim();
          if (!sourceFile) continue;

          const needle = String(msg.query || "").trim();
          const key = `${sourceFile}::${needle}`;
          if (referenceExtras[key]) {
            nextExtras[key] = referenceExtras[key];
            continue;
          }

          const doc = await fetchDoc(sourceFile);
          if (!doc) {
            nextExtras[key] = [];
            continue;
          }

          const pictures = await extractMatchingPicturesFromDoc(doc, sourceFile, needle, ref.score);
          nextExtras[key] = pictures;
        }
      }

      if (!cancelled) {
        setReferenceExtras((prev) => ({ ...prev, ...nextExtras }));
      }
    };

    loadReferenceExtras();
    return () => {
      cancelled = true;
    };
  }, [messages, usePictures, appConfig]);
  const handleSubmit = async (e) => {
    e.preventDefault();
    const input = e.target.elements.messageInput;
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    const userMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    input.value = '';
    setIsLoading(true);
    setIsTyping(true);

    try {
      let relevantResults = [];
      
      // Only perform RAG search if enabled
      if (useRag) {
        console.log('RAG is enabled, performing search...');
        const results = await searchRAG(message);
        // Filter results by relevance score with safe fallback
        const relevanceThreshold = appConfig?.ui?.components?.search?.relevance_threshold || 0.3;
        relevantResults = results.filter(result => result.score > relevanceThreshold);
        
        console.log('Filtered RAG results:', {
          totalResults: results.length,
          relevantResults: relevantResults.length,
          threshold: relevanceThreshold,
          results: relevantResults.map(r => ({
            score: r.score,
            source: r.source_file,
            preview: r.text.substring(0, 100)
          }))
        });
      } else {
        console.log('RAG is disabled, skipping search');
      }

      // Prepare context messages with RAG results
      const contextMessages = prepareContextMessages(
        messages,
        detailedThinking,
        conversationSummary,
        relevantResults
      );

      // Add the new user message with RAG context if available
      let userContent = message;
      if (relevantResults.length > 0) {
        const ragPrefix = appConfig?.ui?.chat?.context?.rag_prefix || 'Relevant information from knowledge base:\n';
        const ragContext = relevantResults.map(r => r.text).join("\n\n");
        userContent = `${message}\n\n${ragPrefix}${ragContext}`;
        console.log('Combined user message with RAG context:', userContent);
      }

      contextMessages.push({
        role: 'user',
        content: userContent
      });

      console.log('Sending context to LLM:', {
        messageCount: contextMessages.length,
        hasRAGContext: relevantResults.length > 0,
        systemMessages: contextMessages.filter(m => m.role === 'system').length,
        contextPreview: contextMessages.map(m => ({
          role: m.role,
          contentPreview: m.content.substring(0, 100) + '...'
        }))
      });

      const response = await fetch(`${configLoader.api.llmServer.url}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          ...configLoader.api.llmServer.headers,
          ...(appConfig?.llm?.base_url?.includes(":8002")
            ? { 'X-LLM-IP': serverIp }
            : {})
        },
        body: JSON.stringify({
          model: appConfig?.llm?.model?.name || "nvidia/Llama-3.1-Nemotron-Nano-4B-v1.1",
          messages: contextMessages,
          stream: false,
          max_tokens: appConfig?.llm?.model?.max_tokens || 512,
          temperature: appConfig?.llm?.model?.temperature || 0.6,
          top_p: appConfig?.llm?.model?.top_p || 0.95
        }),
      });

      if (!response.ok) {
        throw new Error('LLM server is not accessible');
      }

      const data = await response.json();
      const messageContent = data.choices[0].message.content;

      if (!messageContent) {
        throw new Error('Received empty response from LLM server');
      }

      const assistantMessage = {
        role: 'assistant',
        content: messageContent,
        references: useRag ? JSON.stringify(relevantResults) : '',
        showThinking: detailedThinking,
        query: message
      };

      console.log('Received LLM response:', {
        hasReferences: relevantResults.length > 0,
        referenceCount: relevantResults.length,
        thinkingEnabled: detailedThinking,
        responsePreview: messageContent.substring(0, 100) + '...',
        hasThinkingTags: messageContent.includes('<thinking>')
      });

      setMessages(prev => [...prev, assistantMessage]);
      setPictureSearchQuery(message);

      // Update summary after every 3 messages
      if ((messages.length + 2) % 3 === 0) {
        const newSummary = await updateSummary([...messages, userMessage, assistantMessage]);
        setConversationSummary(newSummary);
      }
    } catch (error) {
      setIsTyping(false);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: error.message.includes('LLM server is not accessible') 
          ? 'The LLM server is not accessible at the moment. Please check if the server is running and try again.'
          : 'Sorry, there was an error processing your request. Please try again.',
        references: '',
        showThinking: detailedThinking
      }]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationSummary('');
    setPinnedPicture(null);
    setPictureSearchResults([]);
    setPictureSearchError('');
  };

  const clearRAG = async () => {
    try {
      // Get current RAG status
      const statusResponse = await fetch(`/api/rag-status`);
      const statusData = await statusResponse.json();
      
      // If RAG is empty, just notify the user
      if (statusData.document_count === 0) {
        alert('RAG index is already empty.');
        return;
      }

      // If RAG is not empty, ask for confirmation
      const confirmed = window.confirm('Are you sure you would like to clear the RAG database?');
      if (!confirmed) {
        return;
      }
      
      // Clear the RAG index on the backend
      const response = await fetch(`/api/clear-rag`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to clear RAG');
      }

      const data = await response.json();
      // Don't clear messages array - preserve chat history and context
      
      alert(`Successfully cleared RAG index. Deleted ${data.deleted_chunks} chunks and ${data.deleted_documents} documents.`);
    } catch (error) {
      console.error('Error clearing RAG:', error);
      alert('Failed to clear RAG index. Please check if the RAG server is running on port 8001.');
    }
  };

  const toggleDetailedThinking = () => {
    setDetailedThinking(prev => !prev);
  };


  const downloadJsonFile = (filename, data) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const exportChatAsDoclingDocument = () => {
    const timestamp = new Date().toISOString();
    const safeTimestamp = timestamp.replace(/[:.]/g, '-');
    const texts = [];
    const pictures = [];
    const bodyChildren = [];
    let textIndex = 0;
    let pictureIndex = 0;

    messages.forEach((message, messageIndex) => {
      const textRef = `#/texts/${textIndex}`;
      const roleLabel = message.role === 'assistant' ? 'Assistant' : 'User';
      const textValue = `${roleLabel}: ${String(message.content || '').trim()}`.trim();

      texts.push({
        self_ref: textRef,
        label: 'paragraph',
        text: textValue,
        orig: textValue,
        meta: {
          role: message.role,
          message_index: messageIndex,
          exported_at: timestamp,
        },
      });

      bodyChildren.push({ $ref: textRef });
      textIndex += 1;

      if (message.pinnedPicture) {
        let captionRef = null;
        const captionText = String(message.pinnedPicture.title || message.pinnedPicture.body || 'Pinned image').trim();
        if (captionText) {
          captionRef = `#/texts/${textIndex}`;
          texts.push({
            self_ref: captionRef,
            label: 'caption',
            text: captionText,
            orig: captionText,
            meta: {
              role: message.role,
              message_index: messageIndex,
              exported_at: timestamp,
              kind: 'picture_caption',
            },
          });
          bodyChildren.push({ $ref: captionRef });
          textIndex += 1;
        }

        const pictureRef = `#/pictures/${pictureIndex}`;
        const picture = {
          self_ref: pictureRef,
          label: 'picture',
          captions: captionRef ? [{ $ref: captionRef }] : [],
          annotations: message.pinnedPicture.body
            ? [{ kind: 'description', text: String(message.pinnedPicture.body) }]
            : [],
          prov: message.pinnedPicture.page_no
            ? [{ page_no: message.pinnedPicture.page_no }]
            : [],
          meta: {
            source_file: message.pinnedPicture.source_file || '',
            doc_name: message.pinnedPicture.doc_name || '',
            title: message.pinnedPicture.title || '',
            image_uri: message.pinnedPicture.imageDataUrl || '',
            message_index: messageIndex,
            exported_at: timestamp,
          },
        };
        pictures.push(picture);
        bodyChildren.push({ $ref: pictureRef });
        pictureIndex += 1;
      }
    });

    const doclingDocument = {
      schema_name: 'DoclingDocument',
      version: '1.0.0',
      name: `chat-export-${safeTimestamp}`,
      origin: {
        mimetype: 'application/json',
        binary_hash: null,
        filename: `chat-export-${safeTimestamp}.docling.json`,
        uri: window.location.href,
      },
      texts,
      pictures,
      body: {
        self_ref: '#/body',
        label: 'document',
        children: bodyChildren,
      },
      meta: {
        exported_from: 'chat-ui',
        exported_at: timestamp,
        message_count: messages.length,
        pinned_picture_count: messages.filter((m) => !!m.pinnedPicture).length,
      },
    };

    downloadJsonFile(`chat-export-${safeTimestamp}.docling.json`, doclingDocument);
  };


  const toggleReference = (index) => {
    setExpandedRefs(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const renderMessage = (message) => {
    if (message.role === 'user') {
      return <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>;
    }

    // For assistant messages, handle thinking content and references
    const thinkingRegex = /<(?:think|thinking|reasoning)>([\s\S]*?)<\/(?:think|thinking|reasoning)>/g;
    const parts = message.content.split(thinkingRegex);
    const hasThinkingContent = parts.length > 1;
    const shouldShowThinking = message.showThinking !== undefined ? message.showThinking : detailedThinking;

    const content = parts.map((part, i) => {
      if (i % 2 === 1) {
        // This is thinking content
        const trimmedContent = part.trim();
        return shouldShowThinking && hasThinkingContent && trimmedContent !== '' ? (
          <details key={i} className="thinking-process">
            <summary>Show thinking process</summary>
            <div className="thinking-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{part}</ReactMarkdown>
            </div>
          </details>
        ) : null;
      }
      // This is regular content
      return part ? <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>{part}</ReactMarkdown> : null;
    });

    // Add references section if available

    const references = message.references
      ? (() => {
          try {
            const parsedRefs = JSON.parse(message.references);
            const relevanceThreshold = appConfig?.ui?.components?.search?.relevance_threshold || 0.3;
            const filteredRefs = parsedRefs.filter((ref) => ref.score > relevanceThreshold).slice(0, 5);

            return filteredRefs.length > 0 ? (
              <details className="references-section">
                <summary>Show references</summary>
                {filteredRefs.map((ref, index) => {
                  const extraKey = `${String(ref?.source_file || "").trim()}::${String(message.query || "").trim()}`;
                  const extras = usePictures ? referenceExtras[extraKey] || [] : [];
                  return (
                    <div key={index} className="reference-card">
                      <div className="reference-meta">
                        <span className="reference-score">
                          Relevance: {Math.round(ref.score * 100)}%
                        </span>
                        <a
                          href={`${appConfig?.api?.base_url || "http://localhost:8001"}/api/document/${encodeURIComponent(
                            ref.source_file
                          )}`}
                          target="_blank"
                          rel="noreferrer"
                          className="reference-link"
                        >
                          View Source Document
                        </a>
                      </div>

                      <div
                        className={`reference-text ${
                          ref.text.length > 600 ? (expandedRefs[index] ? "expanded" : "truncated") : ""
                        }`}
                        onClick={ref.text.length > 600 ? () => toggleReference(index) : undefined}
                        style={{ cursor: ref.text.length > 600 ? "pointer" : "default" }}
                      >
                        {ref.text}
                      </div>

                      {ref.text.length > 600 && (
                        <div className="reference-expand-label">
                          {expandedRefs[index] ? "Show less" : "Show more"}
                        </div>
                      )}

                      {usePictures && extras.length > 0 && (
                        <div style={{ marginTop: "0.75rem" }}>
                          {extras.map((item, extraIdx) => (
                            <div
                              key={`${extraKey}-${extraIdx}`}
                              style={{
                                border: "1px solid rgba(255,255,255,0.08)",
                                borderRadius: 8,
                                padding: "10px 12px",
                                marginTop: "0.5rem",
                                background: "rgba(255,255,255,0.02)",
                              }}
                            >
                              <div style={{ fontWeight: 700, marginBottom: "0.35rem" }}>{item.title}</div>
                              {item.imageDataUrl ? (
                                <img
                                  src={item.imageDataUrl}
                                  alt={item.title || "reference picture"}
                                  style={{ maxWidth: "100%", height: "auto", borderRadius: 6, marginBottom: "0.5rem" }}
                                />
                              ) : null}
                              {item.body ? (
                                <div style={{ whiteSpace: "pre-wrap", opacity: 0.95 }}>{item.body}</div>
                              ) : null}
                              <div style={{ marginTop: "0.35rem", opacity: 0.8, fontSize: "0.9em" }}>
                                picture{item.page_no ? ` · page ${item.page_no}` : ""}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </details>
            ) : null;
          } catch (e) {
            return null;
          }
        })()
      : null;

    return (
      <>
        {content}
        {message.pinnedPicture ? (
          <div style={{ marginTop: '0.9rem', maxWidth: 320 }}>
            <div style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.35rem' }}>Pinned image</div>
            {message.pinnedPicture.imageDataUrl ? (
              <img
                src={message.pinnedPicture.imageDataUrl}
                alt={message.pinnedPicture.title || 'pinned picture'}
                style={{ width: '100%', height: 'auto', borderRadius: 8, marginBottom: '0.5rem' }}
              />
            ) : null}
            <div style={{ fontWeight: 700 }}>{message.pinnedPicture.title}</div>
            {message.pinnedPicture.body ? (
              <div style={{ whiteSpace: 'pre-wrap', opacity: 0.92 }}>{message.pinnedPicture.body}</div>
            ) : null}
          </div>
        ) : null}
        {references}
      </>
    );
  };

  return (
    <div className="App">
      <header className="App-header" style={{ paddingBottom: '0.75rem' }}>
        {error && (
          <div className={`error-message ${errorTimeoutRef.current ? 'fade-out' : ''}`} role="alert">
            <span className="error-icon">⚠️</span>
            {error}
            <button
              className="close-button"
              onClick={() => {
                if (errorTimeoutRef.current) {
                  clearTimeout(errorTimeoutRef.current);
                }
                setError(null);
              }}
              aria-label="Close error message"
            >
              ×
            </button>
          </div>
        )}
        <div className="controls">
          <div className="rag-toggle">
            <label className="switch">
              <input
                type="checkbox"
                checked={useRag}
                onChange={(e) => setUseRag(e.target.checked)}
              />
              <span className="slider round"></span>
            </label>
            <span className="toggle-label">Use RAG</span>
          </div>

          <div className="rag-toggle">
            <label className="switch">
              <input
                type="checkbox"
                checked={usePictures}
                onChange={(e) => setUsePictures(e.target.checked)}
              />
              <span className="slider round"></span>
            </label>
            <span className="toggle-label">Use Pictures</span>
          </div>

          <div className="rag-toggle">
            <label className="switch">
              <input
                type="checkbox"
                checked={detailedThinking}
                onChange={toggleDetailedThinking}
              />
              <span className="slider round"></span>
            </label>
            <span className="toggle-label">Use Reasoning</span>
          </div>

          <div className="button-group">
            <button onClick={clearChat}>Clear Chat and Context</button>
            <button onClick={clearRAG}>Clear RAG</button>
            <button onClick={exportChatAsDoclingDocument} disabled={!messages.length}>
              Export Chat
            </button>
            <button onClick={() => setView(view === 'chat' ? 'knowledge' : 'chat')}>
              {view === 'chat' ? 'Open Knowledge' : 'Back to Chat'}
            </button>
          </div>
        </div>
      </header>

      <main className="chat-container">
        {view === 'knowledge' ? (
          <ProjectKnowledge usePictures={usePictures} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: pictureSidecarOpen ? 'minmax(0, 1fr) 340px' : 'minmax(0, 1fr) 56px', gap: '1rem', width: '100%', transition: 'grid-template-columns 0.2s ease' }}>
            <div style={{ minWidth: 0, display: 'flex', flexDirection: 'column' }}>
              <div className="messages" style={{ flex: 1 }}>
                {messages.map((message, index) => (
                  <div key={index} className={`message ${message.role}`}>
                    {renderMessage(message)}
                  </div>
                ))}
                {isTyping && (
                  <div className="message assistant">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <form onSubmit={handleSubmit} className="input-form" style={{ marginTop: '0.85rem' }}>
                <input
                  type="text"
                  name="messageInput"
                  placeholder="What's on your mind?"
                  disabled={isLoading}
                />
                <button type="submit" disabled={isLoading}>
                  {isLoading ? 'Thinking...' : 'Send'}
                </button>
              </form>
            </div>

            <aside style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: pictureSidecarOpen ? '12px' : '8px', background: 'rgba(255,255,255,0.03)', alignSelf: 'start', minHeight: 240, overflow: 'hidden', transition: 'all 0.2s ease' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: pictureSidecarOpen ? 'space-between' : 'center', marginBottom: pictureSidecarOpen ? '0.75rem' : 0 }}>
                {pictureSidecarOpen ? (
                  <div>
                    <div style={{ fontWeight: 700, marginBottom: '0.25rem' }}>Picture Context Search</div>
                    <div style={{ opacity: 0.8, fontSize: '0.9rem' }}>Independent search using the same chunk search flow as Project Knowledge.</div>
                  </div>
                ) : null}
                <button
                  type="button"
                  onClick={() => setPictureSidecarOpen((prev) => !prev)}
                  title={pictureSidecarOpen ? 'Collapse picture search' : 'Open picture search'}
                  aria-label={pictureSidecarOpen ? 'Collapse picture search' : 'Open picture search'}
                  style={{ minWidth: 40, height: 40, borderRadius: 10, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.04)', color: 'inherit', cursor: 'pointer' }}
                >
                  {pictureSidecarOpen ? '→' : '←'}
                </button>
              </div>

              {!pictureSidecarOpen ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', marginTop: '0.5rem' }}>
                  <div style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', letterSpacing: '0.04em', fontSize: '0.78rem', opacity: 0.8 }}>Picture Search</div>
                  {pictureSearchResults[0]?.imageDataUrl ? (
                    <img
                      src={pictureSearchResults[0].imageDataUrl}
                      alt={pictureSearchResults[0].title || 'picture search preview'}
                      style={{ width: 38, height: 38, objectFit: 'cover', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}
                    />
                  ) : null}
                </div>
              ) : (
                <>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      runPictureContextSearch(pictureSearchQuery);
                    }}
                    style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}
                  >
                    <input
                      type="text"
                      value={pictureSearchQuery}
                      onChange={(e) => setPictureSearchQuery(e.target.value)}
                      placeholder="Search picture context"
                      style={{ flex: 1 }}
                    />
                    <button type="submit" disabled={pictureSearchLoading || !pictureSearchQuery.trim()}>
                      {pictureSearchLoading ? 'Searching...' : 'Search'}
                    </button>
                  </form>

                  {pictureSearchError ? (
                    <div style={{ color: '#ffb4b4', marginBottom: '0.75rem' }}>{pictureSearchError}</div>
                  ) : null}

                  <div style={{ display: 'grid', gap: '0.75rem' }}>
                    {pictureSearchResults.map((item, index) => (
                      <div key={`${item.source_file || 'pic'}-${item.page_no || index}-${index}`} style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '10px', background: 'rgba(255,255,255,0.02)' }}>
                        {item.imageDataUrl ? (
                          <img
                            src={item.imageDataUrl}
                            alt={item.title || 'search result picture'}
                            style={{ width: '100%', height: 'auto', borderRadius: 8, marginBottom: '0.5rem' }}
                          />
                        ) : null}
                        <div style={{ fontWeight: 700, marginBottom: '0.25rem' }}>{item.title}</div>
                        {item.body ? (
                          <div style={{ fontSize: '0.92rem', opacity: 0.9, whiteSpace: 'pre-wrap', marginBottom: '0.5rem' }}>{item.body}</div>
                        ) : null}
                        <div style={{ fontSize: '0.82rem', opacity: 0.75, marginBottom: '0.5rem' }}>
                          {item.source_file || item.doc_name || 'source'}
                          {item.page_no ? ` · page ${item.page_no}` : ''}
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button
                            type="button"
                            onClick={() => {
                              pinPictureToChat(item);
                              setMessages((prev) => {
                                const next = [...prev];
                                for (let i = next.length - 1; i >= 0; i -= 1) {
                                  if (next[i].role === 'assistant') {
                                    next[i] = { ...next[i], pinnedPicture: item };
                                    return next;
                                  }
                                }
                                return [...prev, { role: 'assistant', content: 'Pinned related image.', references: '', showThinking: false, pinnedPicture: item }];
                              });
                            }}
                          >
                            Pin to Chat
                          </button>
                          <button
                            type="button"
                            onClick={() => setPictureSidecarOpen(false)}
                          >
                            Fold Away
                          </button>
                        </div>
                      </div>
                    ))}
                    {!pictureSearchLoading && !pictureSearchResults.length && !pictureSearchError ? (
                      <div style={{ opacity: 0.7, fontSize: '0.92rem' }}>Search for a topic to find pictures from Project Knowledge.</div>
                    ) : null}
                  </div>
                </>
              )}
            </aside>
          </div>
        )}
      </main>
    </div>
  );

}

export default App;

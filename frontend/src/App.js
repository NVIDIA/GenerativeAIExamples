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
import PictureAnnotations from './pages/PictureAnnotations';
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
  const [picturePlaceOnly, setPicturePlaceOnly] = useState(false);
  const [, setPinnedPicture] = useState(null);

  // View toggle
  const [view, setView] = useState("chat"); // "chat" | "knowledge" | "pictureAnnotations"

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
      setServerIp("192.168.1.178");
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
    messagesEndRef.current?.scrollIntoView({ behavior: "auto", block: "nearest" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  useEffect(() => {
    const handleClick = (event) => {
      const button = event.target.closest('[data-pin-picture]');
      if (!button) return;
      const key = button.getAttribute('data-pin-picture');
      const item = pictureSearchResults.find(
        (pic) => `${pic.source_file || ''}::${pic.page_no || ''}::${pic.title || ''}` === key
      );
      if (!item) return;
      pinPictureToChat(item);
      setMessages((prev) => {
        const next = [...prev];
        for (let i = next.length - 1; i >= 0; i -= 1) {
          if (next[i].role === 'assistant') {
            next[i] = { ...next[i], pinnedPicture: item };
            return next;
          }
        }
        return prev;
      });
    };

    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [pictureSearchResults]);


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
          max_tokens: 256
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

  const getPictureTextParts = (doc, picture) => {
    const textByRef = getTextByRefMap(doc);
    const captions = Array.isArray(picture?.captions) ? picture.captions : [];

    const captionTexts = captions
      .map((c) => {
        if (typeof c === "string") return c;
        if (!c || typeof c !== "object") return null;
        return c.$ref || c.ref || null;
      })
      .filter(Boolean)
      .map((refOrText) => {
        if (typeof refOrText !== "string") return "";
        return textByRef.get(refOrText) || refOrText;
      })
      .filter((t) => norm(t));

    const directCaptionTexts = captions
      .map((c) => {
        if (typeof c === "string") return "";
        if (!c || typeof c !== "object") return "";
        return c.text || c.orig || c.caption || c.label || "";
      })
      .filter((t) => norm(t))
      .map((t) => norm(t));

    const ann = Array.isArray(picture?.annotations) ? picture.annotations : [];
    const annotationTexts = ann
      .map((a) => {
        if (typeof a === "string") return "";
        if (!a || typeof a !== "object") return "";
        return a?.kind === "description" && norm(a?.text) ? norm(a.text) : "";
      })
      .filter(Boolean);

    const meta = picture?.meta && typeof picture.meta === "object" ? picture.meta : {};
    const metaTexts = [meta.description, meta.caption, meta.desc, meta.place]
      .filter((t) => norm(t))
      .map((t) => norm(t));

    const seen = new Set();
    return [...captionTexts, ...directCaptionTexts, ...annotationTexts, ...metaTexts].filter((t) => {
      const key = normLower(t);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  const getPictureCaption = (doc, picture) => {
    const parts = getPictureTextParts(doc, picture);
    return parts.join("\n\n");
  };

  const getPictureCaptionsOnly = (doc, picture) => {
    const textByRef = getTextByRefMap(doc);
    const captions = Array.isArray(picture?.captions) ? picture.captions : [];
    const seen = new Set();
    return captions.flatMap((c) => {
      if (typeof c === "string") return [norm(c)];
      if (!c || typeof c !== "object") return [];
      const vals = [];
      const ref = c.$ref || c.ref;
      if (ref && textByRef.get(ref)) vals.push(norm(textByRef.get(ref)));
      for (const v of [c.text, c.orig, c.caption]) if (norm(v)) vals.push(norm(v));
      return vals;
    }).filter((x) => {
      const k = normLower(x);
      if (!k || seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  };

  const getPictureAnnotationTexts = (picture) => {
    const ann = Array.isArray(picture?.annotations) ? picture.annotations : [];
    const seen = new Set();
    return ann.map((a) => {
      if (typeof a === "string") return norm(a);
      if (!a || typeof a !== "object") return "";
      return norm(a?.text || "");
    }).filter((x) => {
      const k = normLower(x);
      if (!k || seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  };

  const getPictureClassification = (picture) => {
    const meta = picture?.meta && typeof picture.meta === "object" ? picture.meta : {};
    return norm(meta.picture_classification || meta.classification || meta.pictureClass || "");
  };

  const formatClassificationText = (classification) => {
    return classification ? `Classification: ${classification}` : "";
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
      } else if (typeof imgMeta === "string" && imgMeta) {
        src = imgMeta.startsWith("data:") ? imgMeta : `data:image/png;base64,${imgMeta}`;
      }

      if (!src) return null;

      const img = await new Promise((resolve, reject) => {
        const el = new window.Image();
        el.onload = () => resolve(el);
        el.onerror = reject;
        el.src = src;
      });

      if (!(pxW > 0 && pxH > 0)) {
        pxW = img.naturalWidth || img.width || 0;
        pxH = img.naturalHeight || img.height || 0;
      }
      if (!(pxW > 0 && pxH > 0)) return null;

      const pdfSize = page.size && typeof page.size === "object" ? page.size : {};
      const pdfW = Number(pdfSize.width || 0);
      const pdfH = Number(pdfSize.height || 0);

      let x0 = 0;
      let y0 = 0;
      let x1 = 0;
      let y1 = 0;

      if (pdfW > 0 && pdfH > 0) {
        const l = Number(bbox.l || 0);
        const t = Number(bbox.t || 0);
        const r = Number(bbox.r || 0);
        const b = Number(bbox.b || 0);
        x0 = Math.round((l / pdfW) * pxW);
        x1 = Math.round((r / pdfW) * pxW);
        y0 = Math.round(((pdfH - t) / pdfH) * pxH);
        y1 = Math.round(((pdfH - b) / pdfH) * pxH);
      } else {
        x0 = Number(bbox.l || 0);
        y0 = Number(bbox.t || 0);
        x1 = Number(bbox.r || 0);
        y1 = Number(bbox.b || 0);
      }

      const xs = [x0, x1].sort((a, b) => a - b);
      const ys = [y0, y1].sort((a, b) => a - b);
      x0 = Math.max(0, Math.round(xs[0] - padPx));
      x1 = Math.min(Math.round(pxW), Math.round(xs[1] + padPx));
      y0 = Math.max(0, Math.round(ys[0] - padPx));
      y1 = Math.min(Math.round(pxH), Math.round(ys[1] + padPx));

      if (x1 - x0 < 2 || y1 - y0 < 2) return null;

      const canvas = document.createElement("canvas");
      canvas.width = x1 - x0;
      canvas.height = y1 - y0;
      const ctx = canvas.getContext("2d");
      if (!ctx) return null;
      ctx.drawImage(img, x0, y0, x1 - x0, y1 - y0, 0, 0, x1 - x0, y1 - y0);
      return canvas.toDataURL("image/png");
    } catch (_) {
      return null;
    }
  };
  const fetchDoc = async (sourceFile) => {
    const baseUrl = appConfig?.api?.base_url || "http://192.168.1.178:8001";
    const resp = await fetch(`${baseUrl}/api/document/${encodeURIComponent(sourceFile)}`, {
      headers: { Accept: "application/json" },
    });
    if (!resp.ok) return null;
    return await resp.json();
  };


  const escapeHtml = (s) =>
    String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const escapeRegExp = (s) => String(s || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  const highlightHtml = (text, needle) => {
    const safeText = escapeHtml(text);
    const q = String(needle || "").trim();
    if (!q) return safeText;
    const re = new RegExp(`(${escapeRegExp(q)})`, "ig");
    return safeText.replace(re, '<mark class="pk-highlight">$1</mark>');
  };

  const linkifyHtml = (html) =>
    String(html || "").replace(
      /(https?:\/\/[A-Za-z0-9._~:/?#[\]@!$&'()*+,;=%-]+)/g,
      '<a href="$1" target="_blank" rel="noreferrer">$1</a>'
    );

  const renderPictureSearchCardsHtml = (cards, highlightNeedle) => {
    if (!cards.length) return `<div class="pk-empty">No rendered picture results.</div>`;
    return cards
      .map((card) => {
        const title = linkifyHtml(highlightHtml(card.title, highlightNeedle));
        const body = linkifyHtml(highlightHtml(card.body, highlightNeedle));
        const relevance = card.score != null ? `Relevance: ${Math.round(card.score * 100)}%` : "Relevance: â";
        const footer = [
          card.kind ? `Type: ${card.kind}` : null,
          card.doc_name ? `Name: ${card.doc_name}` : null,
          Number.isInteger(card.page_no) ? `Page: ${card.page_no}` : null,
          ...(Array.isArray(card.footer) ? card.footer : []),
        ]
          .filter(Boolean)
          .map((item) => `<span>${linkifyHtml(highlightHtml(item, highlightNeedle))}</span>`)
          .join("");

        const viewSource = card.source_file
          ? `<a class="pk-view-source-btn" href="${escapeHtml(`${appConfig?.api?.base_url || "http://192.168.1.178:8001"}/api/document/${encodeURIComponent(card.source_file)}`)}" target="_blank" rel="noreferrer">View Source Document</a>`
          : "";
        const imageBlock = card.imageDataUrl
          ? `<div class="pk-reference-image-wrap"><img class="pk-reference-image" src="${escapeHtml(card.imageDataUrl)}" alt="${escapeHtml(card.title || "picture")}" /></div>`
          : "";
        const pinKey = `${card.source_file || ''}::${card.page_no || ''}::${card.title || ''}`;

        return `
          <div class="pk-reference-card">
            <div class="pk-reference-header">
              <div class="pk-reference-meta">
                <div class="pk-reference-score">${escapeHtml(relevance)}</div>
                <div class="pk-reference-title">${title}</div>
              </div>
              ${viewSource}
            </div>
            ${imageBlock}
            <div class="pk-reference-body">${body}</div>
            ${footer ? `<div class="pk-reference-footer">${footer}</div>` : ""}
            <div style="margin-top: 10px; display: flex; gap: 8px;">
              <button type="button" data-pin-picture="${escapeHtml(pinKey)}" class="pk-pin-btn">Pin to Chat</button>
            </div>
          </div>
        `;
      })
      .join("");
  };

  const projectKnowledgeResultCss = `
    .pk-results-wrap { margin-top: 1rem; }
    .pk-results-panel { background: #d9d9dd; border-radius: 8px; padding: 10px; color: #202124; }
    .pk-results-title { margin: 0 0 0.5rem 0; color: inherit; font-size: 1.1rem; font-weight: 600; }
    .pk-empty { color: #4a4a4a; padding: 8px 4px; }
    .pk-highlight { background: rgba(255, 230, 0, 0.35); color: inherit; padding: 0 2px; border-radius: 2px; }
    .pk-reference-card { background: #efefef; border: 1px solid #d6d6d6; border-radius: 6px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08); padding: 12px; margin-top: 12px; color: #222; }
    .pk-reference-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
    .pk-reference-meta { min-width: 0; flex: 1; }
    .pk-reference-score { font-size: 0.95rem; color: #6a6a6a; margin-bottom: 4px; }
    .pk-reference-title { font-size: 1rem; font-weight: 500; line-height: 1.45; color: #2b2b2b; white-space: pre-wrap; word-break: break-word; }
    .pk-view-source-btn, .pk-pin-btn { display: inline-flex; align-items: center; justify-content: center; white-space: nowrap; padding: 6px 12px; border-radius: 4px; border: 1px solid #6d3ea2; color: #6d3ea2; background: #f8f6fb; text-decoration: none; font-size: 0.9rem; line-height: 1.2; cursor: pointer; }
    .pk-view-source-btn:hover, .pk-pin-btn:hover { background: #f1ecf8; }
    .pk-reference-body { white-space: pre-wrap; line-height: 1.7; color: #303030; overflow-wrap: anywhere; }
    .pk-reference-footer { margin-top: 10px; font-size: 0.88rem; color: #666; display: flex; flex-wrap: wrap; gap: 10px; }
    .pk-reference-image-wrap { margin: 0 0 12px 0; }
    .pk-reference-image { max-width: 100%; height: auto; display: block; border-radius: 8px; border: 1px solid #d6d6d6; background: #fff; }
  `;


  const getDoclingPicturePlace = (picture) => {
    return String(picture?.meta?.place || "").trim();
  };

  const getDoclingMaterialsText = (doc) => {
    const texts = Array.isArray(doc?.texts) ? doc.texts : [];
    return texts
      .map((item) => String(item?.text || "").trim())
      .filter((value) => /^MATERIALS\s*:/i.test(value))
      .join(" | ");
  };

  const getDoclingTableText = (doc) => {
    const tables = Array.isArray(doc?.tables) ? doc.tables : [];
    const parts = [];

    for (const table of tables) {
      const cells = Array.isArray(table?.data?.table_cells) ? table.data.table_cells : [];
      for (const cell of cells) {
        const value = String(cell?.text || "").trim();
        if (value) parts.push(value);
      }
    }

    return parts.join(" | ");
  };

  const getDoclingMatchText = (doc, picture) => {
    const captionText = String(getPictureCaption(doc, picture) || "").trim();
    const picturePlace = getDoclingPicturePlace(picture);
    const docName = String(doc?.name || "").trim();
    const materialsText = getDoclingMaterialsText(doc);
    const tableText = getDoclingTableText(doc);

    return [
      captionText,
      picturePlace,
      docName,
      materialsText,
      tableText,
    ]
      .filter(Boolean)
      .join(" | ");
  };

  const pictureQueryTokens = (value) => {
    const stop = new Set([
      "the","and","for","with","that","this","from","into","about","using","what","when","where",
      "which","whose","then","than","they","them","their","have","has","had","was","were","are",
      "you","your","assistant","user","answer","based","does","did","show","tell","give","find",
      "building","picture","image","photo","materials","material"
    ]);
    return [...new Set(
      normLower(value)
        .split(/[^a-z0-9]+/g)
        .filter((token) => token && token.length >= 3 && !stop.has(token))
    )];
  };

  const pictureMatchScore = (doc, picture, needle, options = {}) => {
    const placeOnly = !!options.placeOnly;
    const rawNeedle = String(needle || "").trim();
    const cleanedNeedle = rawNeedle.replace(/^place\s*:\s*/i, "").trim();
    const haystack = normLower(getDoclingMatchText(doc, picture));
    const placeText = normLower(getDoclingPicturePlace(picture));
    const queryNorm = normLower(cleanedNeedle);
    const tokens = pictureQueryTokens(cleanedNeedle);

    if (placeOnly) {
      if (!placeText) return 0;
      if (queryNorm && placeText === queryNorm) return 100;
      if (!tokens.length) return placeText ? 1 : 0;
      let placeHits = 0;
      for (const token of tokens) {
        if (placeText.includes(token)) placeHits += 1;
      }
      return placeHits;
    }

    if (!tokens.length) return haystack ? 1 : 0;

    let hits = 0;
    for (const token of tokens) {
      if (haystack.includes(token)) hits += 1;
    }

    if (placeText && queryNorm) {
      if (placeText === queryNorm) hits += 100;
      else {
        let placeHits = 0;
        for (const token of tokens) {
          if (placeText.includes(token)) placeHits += 1;
        }
        hits += placeHits * 3;
      }
    }

    return hits;
  };

  const stripAssistantIntroPreamble = (content) => {
  let text = String(content || "").trim();
  if (!text) return text;

  const lines = text.split("\n");
  let cut = -1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (
      line.match(/^\d+\./) ||        // 1. Heading
      line.startsWith("- ") ||        // bullet
      line.startsWith("* ") ||
      (line.includes(":") && line.length < 120) // section label like "Location & Context:"
    ) {
      cut = i;
      break;
    }
  }

  if (cut > 0) {
    return lines.slice(cut).join("\n").trim();
  }

  return text;
};


  const getImageSizeFromDataUrl = async (src) => {
    try {
      if (!src) return null;
      return await new Promise((resolve) => {
        const img = new window.Image();
        img.onload = () => resolve({
          width: Number(img.naturalWidth || img.width || 0),
          height: Number(img.naturalHeight || img.height || 0),
        });
        img.onerror = () => resolve(null);
        img.src = src;
      });
    } catch (_) {
      return null;
    }
  };

  const isLikelyLogoPicture = async (doc, picture, imageDataUrl, pageNo, bbox) => {
    try {
      const pictureText = normLower(getPictureCaption(doc, picture));
      const picturePlace = normLower(getDoclingPicturePlace(picture));
      const titleish = normLower(picture?.title || "");
      const allText = [pictureText, picturePlace, titleish].filter(Boolean).join(" ");

      // HARD reject logos (critical fix)
      if (
        allText.includes("historic england") ||
        allText.includes("logo") ||
        allText.includes("wordmark") ||
        allText.includes("crest")
      ) {
        return true;
      }


      if (/\b(logo|wordmark|brand mark|brandmark|letterhead|header logo|footer logo)\b/i.test(allText)) {
        return true;
      }

      const size = await getImageSizeFromDataUrl(imageDataUrl);
      const iw = Number(size?.width || 0);
      const ih = Number(size?.height || 0);
      const area = iw * ih;

      const page = getPageObject(doc, pageNo);
      const pageSize = page?.size && typeof page.size === "object" ? page.size : {};
      const pdfW = Number(pageSize.width || 0);
      const pdfH = Number(pageSize.height || 0);

      const l = Number(bbox?.l || 0);
      const t = Number(bbox?.t || 0);
      const r = Number(bbox?.r || 0);
      const b = Number(bbox?.b || 0);
      const bw = Math.max(0, r - l);
      const bh = Math.max(0, t - b);

      const topBand = pdfH > 0 ? t >= (pdfH * 0.88) : false;
      const bottomBand = pdfH > 0 ? b <= (pdfH * 0.12) : false;
      const edgeBand = topBand || bottomBand;

      const boxArea = bw * bh;
      const pageArea = pdfW > 0 && pdfH > 0 ? pdfW * pdfH : 0;
      const areaRatio = pageArea > 0 ? (boxArea / pageArea) : 0;

      if (bw > 0 && bh > 0) {
        const boxAspect = bw / Math.max(bh, 1);
        if (boxAspect >= 4.5 && bh <= 120) return true;
        if (areaRatio > 0 && areaRatio < 0.01 && edgeBand) return true;
      }

      if (iw > 0 && ih > 0) {
        const imgAspect = iw / Math.max(ih, 1);
        if (imgAspect >= 4.5 && ih <= 140) return true;
        if (area > 0 && area < 25000 && edgeBand) return true;
      }

      return false;
    } catch (_) {
      return false;
    }
  };

  const extractMatchingPicturesFromDoc = async (doc, sourceFile, needle, score = null, options = {}) => {
    const out = [];
    const pictures = Array.isArray(doc?.pictures) ? doc.pictures : [];
    const materialsText = getDoclingMaterialsText(doc);

    for (let i = 0; i < pictures.length; i++) {
      const picture = pictures[i];
      if (!picture || typeof picture !== "object") continue;

      const combinedText = String(getPictureCaption(doc, picture) || "").trim();
      const picturePlace = getDoclingPicturePlace(picture);
      const captionTexts = getPictureCaptionsOnly(doc, picture);
      const annotationTexts = getPictureAnnotationTexts(picture);
      const pictureClassification = getPictureClassification(picture);
      const matchHits = pictureMatchScore(doc, picture, needle, options);

      if (String(needle || "").trim() && matchHits <= 0) continue;

      const pageNo = getPageNo(picture);
      const bbox = getItemBbox(picture);
      const imageDataUrl = await cropPictureFromPage(doc, pageNo, bbox);

      if (await isLikelyLogoPicture(doc, picture, imageDataUrl, pageNo, bbox)) {
        continue;
      }

      const titleText =
        captionTexts[0] ||
        picturePlace ||
        combinedText ||
        doc?.name ||
        `picture ${i + 1}`;

      const bodyParts = [];

      const classificationText = formatClassificationText(pictureClassification);
      if (classificationText) {
        bodyParts.push(classificationText);
      }

      if (captionTexts.length) {
        const filteredCaptions = captionTexts.filter((c) => normLower(c) !== normLower(titleText));
        if (filteredCaptions.length) {
          bodyParts.push(`Captions:\n${filteredCaptions.join("\n")}`);
        }
      }

      if (annotationTexts.length) {
        bodyParts.push(`Annotations:\n${annotationTexts.join("\n")}`);
      }

      if (materialsText) {
        bodyParts.push(`Materials: ${materialsText.replace(/^MATERIALS\s*:/i, "").trim()}`);
      }

      out.push({
        kind: "picture",
        title: titleText,
        body: bodyParts.length ? bodyParts.join("\n\n") : "",
        imageDataUrl,
        page_no: pageNo,
        source_file: sourceFile,
        doc_name: doc?.name || "",
        score: matchHits > 0 ? Math.max(Number(score || 0), matchHits / 10) : score,
        footer: [
          picturePlace ? `Place: ${picturePlace}` : null,
          picture?.self_ref ? `Ref: ${picture.self_ref}` : null
        ].filter(Boolean),
      });
    }

    return out;
  };
  const buildPictureResultsFromSearch = async (query, refs, options = {}) => {
    const out = [];
    const seen = new Set();

    // Do not rely too heavily on backend chunk relevance because
    // picture annotations/meta may not be indexed by /api/search.
    const candidateRefs = Array.isArray(refs) ? refs.slice(0, 50) : [];
    const sourceFiles = [];
    const sourceSeen = new Set();

    for (const ref of candidateRefs) {
      const sourceFile = String(ref?.source_file || "").trim();
      if (!sourceFile || sourceSeen.has(sourceFile)) continue;
      sourceSeen.add(sourceFile);
      sourceFiles.push({ sourceFile, score: ref?.score ?? null });
      if (sourceFiles.length >= 20) break;
    }

    for (const { sourceFile, score } of sourceFiles) {
      const doc = await fetchDoc(sourceFile);
      if (!doc) continue;

      const pictures = await extractMatchingPicturesFromDoc(doc, sourceFile, query, score, options);
      if (!pictures.length) continue;

      for (const picture of pictures) {
        const key = `${picture.source_file || ""}::${picture.page_no || ""}::${picture.title || ""}`;
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(picture);
        if (out.length >= 20) return out;
      }
    }

    return out;
  };

  const searchChunks = async (query, options = {}) => {
    if (!appConfig) return [];

    const cleanQuery = String(query || '').trim();
    if (!cleanQuery) return [];

    const k = Number.isInteger(options.k) ? options.k : (appConfig?.ui?.components?.search?.default_k || 5);
    const baseUrl = appConfig?.api?.base_url || 'http://192.168.1.178:8001';
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
      const refs = await searchChunks(cleanQuery, { k: 50 });
      const pictures = await buildPictureResultsFromSearch(cleanQuery, refs, { placeOnly: picturePlaceOnly });
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, usePictures, appConfig]);
  const handleSubmit = async (e) => {
    e.preventDefault();
    const input = e.target.elements.messageInput;
    const message = input.value.trim();

    if (!message) return;

    const userMessage = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMessage]);
    input.value = '';
    setIsLoading(true);
    setIsTyping(true);

    try {
      let relevantResults = [];

      if (useRag) {
        console.log('RAG is enabled, performing search...');
        const results = await searchRAG(message);

        const relevanceThreshold =
          appConfig?.ui?.components?.search?.relevance_threshold || 0.3;

        relevantResults = results.filter((result) => result.score > relevanceThreshold);

        console.log('Filtered RAG results:', {
          totalResults: results.length,
          relevantResults: relevantResults.length,
          threshold: relevanceThreshold,
          results: relevantResults.map((r) => ({
            score: r.score,
            source: r.source_file,
            preview: r.text.substring(0, 100),
          })),
        });
      } else {
        console.log('RAG is disabled, skipping search');
      }

      const contextMessages = prepareContextMessages(
        messages,
        detailedThinking,
        conversationSummary,
        relevantResults
      );

      let userContent = message;
      if (relevantResults.length > 0) {
        const ragPrefix =
          appConfig?.ui?.chat?.context?.rag_prefix ||
          'Relevant information from knowledge base:\n';
        const ragContext = relevantResults.map((r) => r.text).join('\n\n');
        userContent = `${message}\n\n${ragPrefix}${ragContext}`;
        console.log('Combined user message with RAG context:', userContent);
      }

      contextMessages.push({
        role: 'user',
        content: userContent,
      });

      console.log('Sending context to LLM:', {
        messageCount: contextMessages.length,
        hasRAGContext: relevantResults.length > 0,
        systemMessages: contextMessages.filter((m) => m.role === 'system').length,
        contextPreview: contextMessages.map((m) => ({
          role: m.role,
          contentPreview: m.content.substring(0, 100) + '...',
        })),
      });

      const response = await fetch(`${configLoader.api.llmServer.url}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          ...configLoader.api.llmServer.headers,
          ...(appConfig?.llm?.base_url?.includes(':8002') ? { 'X-LLM-IP': serverIp } : {}),
        },
        body: JSON.stringify({
          model: appConfig?.llm?.model?.name || 'nvidia/Llama-3.1-Nemotron-Nano-4B-v1.1',
          messages: contextMessages,
          stream: false,
          max_tokens: 256,
          temperature: appConfig?.llm?.model?.temperature || 0.6,
          top_p: appConfig?.llm?.model?.top_p || 0.95,
        }),
      });

      if (!response.ok) {
        throw new Error('LLM server is not accessible');
      }

      const data = await response.json();
      const rawMessageContent = data.choices[0].message.content;
      const messageContent = stripAssistantIntroPreamble(rawMessageContent);

      if (!messageContent) {
        throw new Error('Received empty response from LLM server');
      }

      const assistantMessage = {
        role: 'assistant',
        content: messageContent,
        references: useRag ? JSON.stringify(relevantResults) : '',
        showThinking: detailedThinking,
        query: message,
      };

      console.log('Received LLM response:', {
        hasReferences: relevantResults.length > 0,
        referenceCount: relevantResults.length,
        thinkingEnabled: detailedThinking,
        responsePreview: messageContent.substring(0, 100) + '...',
        hasThinkingTags: messageContent.includes('<thinking>'),
      });

      let assistantMessageWithPicture = assistantMessage;
      setPictureSearchQuery(message);

      if (usePictures) {
        try {
          const pictureQuery = [message, messageContent].filter(Boolean).join('\n');
          const extraRefs = await searchChunks(pictureQuery, { k: 50 });
          const mergedRefs = [...relevantResults, ...extraRefs];
          const dedupedRefs = [];
          const seenRefKeys = new Set();

          for (const ref of mergedRefs) {
            const key = `${String(ref?.source_file || '')}::${String(ref?.text || '').slice(0, 120)}`;
            if (seenRefKeys.has(key)) continue;
            seenRefKeys.add(key);
            dedupedRefs.push(ref);
          }

          const pictures = await buildPictureResultsFromSearch(pictureQuery, dedupedRefs);

          setPictureSearchResults(pictures);

          if (!pictures.length) {
            setPictureSearchError('No matching pictures found for this query.');
          } else {
            setPictureSearchError('');

            const bestPicture = [...pictures].sort(
              (a, b) => (Number(b.score) || 0) - (Number(a.score) || 0)
            )[0];

            if (bestPicture) {
              const pinnedPicture = {
                ...bestPicture,
                url: bestPicture?.image || bestPicture?.url || bestPicture?.src || bestPicture?.imageDataUrl || null,
              };

              pinPictureToChat(pinnedPicture);
              assistantMessageWithPicture = {
                ...assistantMessage,
                pinnedPicture,
              };
            }
          }
        } catch (pictureError) {
          console.error('Auto picture search failed:', pictureError);
          setPictureSearchResults([]);
          setPictureSearchError('Picture search failed.');
        }
      }

      setMessages((prev) => [...prev, assistantMessageWithPicture]);

      if ((messages.length + 2) % 3 === 0) {
        const newSummary = await updateSummary([...messages, userMessage, assistantMessageWithPicture]);
        setConversationSummary(newSummary);
      }
    } catch (error) {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: error.message.includes('LLM server is not accessible')
            ? 'The LLM server is not accessible at the moment. Please check if the server is running and try again.'
            : 'Sorry, there was an error processing your request. Please try again.',
          references: '',
          showThinking: detailedThinking,
        },
      ]);
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
          // Do not push caption into bodyChildren; the picture already references it
          // through picture.captions, and adding it here causes duplicate rendering in
          // consumers that display both standalone body text nodes and picture captions.
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
                          href={`${appConfig?.api?.base_url || "http://192.168.1.178:8001"}/api/document/${encodeURIComponent(
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
                                picture{item.page_no ? ` Â· page ${item.page_no}` : ""}
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
            <span className="error-icon">â ï¸</span>
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
              Ã
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
            <button onClick={() => setView(view === 'pictureAnnotations' ? 'chat' : 'pictureAnnotations')}>
              {view === 'pictureAnnotations' ? 'Back to Chat' : 'Open Picture Annotations'}
            </button>
          </div>
        </div>
      </header>

      <main className="chat-container">
        {view === 'knowledge' ? (
          <ProjectKnowledge usePictures={usePictures} />
        ) : view === 'pictureAnnotations' ? (
          <PictureAnnotations />
        ) : (
          <div className="chat-view-stack">
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

                    <div className="rag-toggle" style={{ marginBottom: "0.75rem" }}>
                      <label className="switch">
                        <input type="checkbox" checked={picturePlaceOnly} onChange={(e) => setPicturePlaceOnly(e.target.checked)} />
                        <span className="slider round"></span>
                      </label>
                      <span className="toggle-label">Place only</span>
                    </div>

            {usePictures ? (
              <section className="picture-context-section">
                <style>{projectKnowledgeResultCss}</style>
                <div className="pk-results-wrap">
                  <div className="pk-results-panel">
                    <div className="pk-results-title picture-context-title">Picture Context Search</div>
                    <div style={{ color: '#4a4a4a', fontSize: '0.95rem', marginBottom: '0.75rem' }}>
                      Rendered with the same card style used in Project Knowledge.
                    </div>

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
                      <div style={{ color: '#8a2d2d', marginBottom: '0.75rem' }}>{pictureSearchError}</div>
                    ) : null}

                    <div dangerouslySetInnerHTML={{ __html: renderPictureSearchCardsHtml(pictureSearchResults, pictureSearchQuery) }} />
                  </div>
                </div>
              </section>
            ) : null}
          </div>        )}
      </main>
    </div>
  );

}

export default App;
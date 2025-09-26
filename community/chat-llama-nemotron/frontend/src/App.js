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
import FileIngestion from './components/FileIngestion';
import configLoader from './config/config_loader';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [detailedThinking, setDetailedThinking] = useState(false);
  const [conversationSummary, setConversationSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [expandedRefs, setExpandedRefs] = useState({});
  const [appConfig, setAppConfig] = useState(null);
  const [serverIp, setServerIp] = useState(() => {
    // Load IP from localStorage on initial render
    const savedIp = localStorage.getItem('serverIp') || '';
    return savedIp;
  });
  const [showIp, setShowIp] = useState(false);
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
          'X-LLM-IP': serverIp
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
          max_tokens: appConfig?.llm?.model?.max_tokens || 350
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
      
      const response = await fetch(`${configLoader.api.proxy}/api/search`, {
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    const input = e.target.elements.messageInput;
    const message = input.value.trim();
    
    if (!message) return;
    
    if (!serverIp) {
      setError('Please enter the IP address of the NVIDIA Dynamo server before sending messages.');
      return;
    }
    
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
          'X-LLM-IP': serverIp
        },
        body: JSON.stringify({
          model: appConfig?.llm?.model?.name || "nvidia/Llama-3.1-Nemotron-Nano-4B-v1.1",
          messages: contextMessages,
          stream: false,
          max_tokens: appConfig?.llm?.model?.max_tokens || 28000,
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
        showThinking: detailedThinking
      };

      console.log('Received LLM response:', {
        hasReferences: relevantResults.length > 0,
        referenceCount: relevantResults.length,
        thinkingEnabled: detailedThinking,
        responsePreview: messageContent.substring(0, 100) + '...',
        hasThinkingTags: messageContent.includes('<thinking>')
      });

      setMessages(prev => [...prev, assistantMessage]);

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
  };

  const clearRAG = async () => {
    try {
      // Get current RAG status
      const statusResponse = await fetch(`http://localhost:8001/api/rag-status`);
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
      const response = await fetch(`http://localhost:8001/api/clear-rag`, {
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
    const references = message.references ? (() => {
      try {
        const parsedRefs = JSON.parse(message.references);
        const relevanceThreshold = appConfig?.ui?.components?.search?.relevance_threshold || 0.3;
        const filteredRefs = parsedRefs.filter(ref => ref.score > relevanceThreshold);
        
        // Only show references section if there are filtered references
        return filteredRefs.length > 0 ? (
          <details className="references">
            <summary>Show references</summary>
            <div className="references-content">
              {filteredRefs.map((ref, index) => (
                <div key={index} className="reference-item">
                  <div className="reference-score">Relevance: {Math.round(ref.score * 100)}%</div>
                  <div className="reference-document">
                    <a 
                      href={`${configLoader.api.proxy}/api/document/${ref.source_file}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="document-link"
                    >
                      View Source Document
                    </a>
                  </div>
                  <div 
                    className={`reference-text ${
                      ref.text.length > 600 
                        ? (expandedRefs[index] ? 'expanded' : 'truncated')
                        : ''
                    }`}
                    onClick={ref.text.length > 600 ? () => toggleReference(index) : undefined}
                    style={{ cursor: ref.text.length > 600 ? 'pointer' : 'default' }}
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {ref.text}
                    </ReactMarkdown>
                    {!expandedRefs[index] && ref.text.length > 600 && (
                      <div className="expand-button">
                        Show more
                      </div>
                    )}
                    {expandedRefs[index] && ref.text.length > 600 && (
                      <div className="expand-button">
                        Show less
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </details>
        ) : null;
      } catch (error) {
        return null;
      }
    })() : null;

    return (
      <>
        {content}
        {references}
      </>
    );
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Chat with Llama-3.1-Nemotron-Nano-4B-v1.1</h1>
        <div className="server-ip-input">
          <label htmlFor="serverIp">NVIDIA Dynamo server:</label>
          <div className="ip-input-container">
            <input
              type={showIp ? "text" : "password"}
              id="serverIp"
              value={serverIp}
              onChange={(e) => {
                setServerIp(e.target.value);
              }}
              placeholder="Enter server IP"
            />
            <button
              type="button"
              className="toggle-ip-visibility"
              onClick={() => setShowIp(!showIp)}
              title={showIp ? "Hide IP address" : "Show IP address"}
            >
              {showIp ? "👁️" : "👁️‍🗨️"}
            </button>
          </div>
        </div>
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
          </div>
        </div>
      </header>

      <main className="chat-container">
        <FileIngestion />
        
        <div className="messages">
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

        <form onSubmit={handleSubmit} className="input-form">
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
      </main>
    </div>
  );
}

export default App;

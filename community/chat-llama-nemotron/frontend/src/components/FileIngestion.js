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


import React, { useState, useEffect, useRef } from 'react';
import './FileIngestion.css';
import configLoader from '../config/config_loader';

function FileIngestion() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [error, setError] = useState(null);
  const [appConfig, setAppConfig] = useState(null);
  const fileInputRef = useRef(null);
  const errorTimeoutRef = useRef(null);

  useEffect(() => {
    // Load configuration
    const loadConfig = async () => {
      try {
        const loadedConfig = await configLoader.getAppConfig();
        if (loadedConfig) {
          setAppConfig(loadedConfig);
        }
      } catch (error) {
        console.error('Error loading config:', error);
      }
    };
    loadConfig();
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    let eventSource;
    if (currentJobId) {
      // Use local RAG server for progress tracking
      eventSource = new EventSource(`http://localhost:8001/api/upload/progress/${currentJobId}`);
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress update:', data);
        
        if (data.type === 'processing') {
          if (data.stage === 'progress') {
            // Smoothly update progress
            const targetProgress = data.progress_percent;
            const currentProgress = uploadProgress;
            
            // If the jump is too large, animate it
            if (Math.abs(targetProgress - currentProgress) > 5) {
              const step = (targetProgress - currentProgress) / 5;
              let current = currentProgress;
              
              const animate = () => {
                current += step;
                if ((step > 0 && current >= targetProgress) || 
                    (step < 0 && current <= targetProgress)) {
                  setUploadProgress(targetProgress);
                } else {
                  setUploadProgress(current);
                  requestAnimationFrame(animate);
                }
              };
              
              requestAnimationFrame(animate);
            } else {
              setUploadProgress(targetProgress);
            }
            
            // Update status message if provided
            if (data.message) {
              setUploadStatus(data.message);
            }
          }
        } else if (data.type === 'complete') {
          setUploadProgress(100);
          setUploadStatus(appConfig?.ui?.components?.file_upload?.messages?.complete || 'Processing complete');
          eventSource.close();
          setCurrentJobId(null);
          // Reset the file input
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
          // Reset all states after a short delay
          setTimeout(() => {
            setUploadStatus('');
            setUploadProgress(0);
            setIsUploading(false);
            setIsDragging(false);
          }, appConfig?.ui?.components?.file_upload?.timeouts?.status_reset || 2000);
        } else if (data.type === 'error') {
          setError(appConfig?.ui?.components?.file_upload?.messages?.error || 'Connection error. Please try again.');
          eventSource.close();
          setCurrentJobId(null);
          // Reset the file input
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
          // Reset all states after a short delay
          setTimeout(() => {
            setUploadStatus('');
            setUploadProgress(0);
            setIsUploading(false);
            setIsDragging(false);
          }, appConfig?.ui?.components?.file_upload?.timeouts?.error_reset || 2000);
        }
      };
      
      eventSource.onerror = () => {
        console.error('EventSource failed');
        eventSource.close();
        setCurrentJobId(null);
        // Reset the file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        setError(appConfig?.ui?.components?.file_upload?.messages?.error || 'Connection error. Please try again.');
        // Reset all states after a short delay
        setTimeout(() => {
          setUploadStatus('');
          setUploadProgress(0);
          setIsUploading(false);
          setIsDragging(false);
        }, appConfig?.ui?.components?.file_upload?.timeouts?.error_reset || 2000);
      };
    }
    
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentJobId, appConfig]);

  // Clean up timeouts on unmount
  useEffect(() => {
    return () => {
      if (errorTimeoutRef.current) {
        clearTimeout(errorTimeoutRef.current);
      }
    };
  }, []);

  // Handle error auto-dismissal
  useEffect(() => {
    if (error) {
      if (errorTimeoutRef.current) {
        clearTimeout(errorTimeoutRef.current);
      }
      errorTimeoutRef.current = setTimeout(() => {
        setError(null);
      }, 3000);
    }
  }, [error]);

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!isUploading) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const uploadFiles = async (files) => {
    try {
      setIsUploading(true);
      setUploadProgress(0);
      setUploadStatus(appConfig?.ui?.components?.file_upload?.messages?.starting || 'Starting upload...');
      
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      // Use local RAG server for file upload
      const response = await fetch(`http://localhost:8001/api/upload`, {
        method: 'POST',
        body: formData,
      }).catch(error => {
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
          throw new Error('RAG server is not accessible. Please check if the RAG server is running on port 8001.');
        }
        throw error;
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      setCurrentJobId(result.job_id);
      setUploadStatus(appConfig?.ui?.components?.file_upload?.messages?.processing || 'Processing files...');
      
    } catch (error) {
      console.error('Upload error:', error);
      setError(error.message.includes('Server is not accessible') 
        ? 'Server is not accessible. Please check if the server is running and try again.'
        : (appConfig?.ui?.components?.file_upload?.messages?.error || 'Connection error. Please try again.'));
      setUploadProgress(0);
      // Reset the file input on error
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setTimeout(() => {
        setUploadStatus('');
        setIsUploading(false);
      }, appConfig?.ui?.components?.file_upload?.timeouts?.error_reset || 3000);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (isUploading) return;
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;
    await uploadFiles(files);
  };

  const handleFileSelect = async (e) => {
    if (isUploading) return;
    
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    await uploadFiles(files);
  };

  return (
    <div 
      className={`file-upload-area ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        id="fileInput"
        multiple
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        disabled={isUploading}
      />
      <label 
        htmlFor="fileInput" 
        className={`upload-button ${isUploading ? 'disabled' : ''}`}
        style={{ pointerEvents: isUploading ? 'none' : 'auto' }}
      >
        {isUploading ? 'Uploading...' : 'Ingest Files'}
      </label>
      <div className="progress-container">
        {isUploading && !error && (
          <>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            {uploadStatus && <div className="upload-status">{uploadStatus}</div>}
          </>
        )}
      </div>
      {error && (
        <div className="error" role="alert">
          {error}
          <button 
            className="close-button" 
            onClick={() => {
              if (errorTimeoutRef.current) {
                clearTimeout(errorTimeoutRef.current);
                errorTimeoutRef.current = null;
              }
              setError(null);
              setUploadStatus('');
              setUploadProgress(0);
              setIsUploading(false);
            }}
            aria-label="Close error message"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default FileIngestion; 
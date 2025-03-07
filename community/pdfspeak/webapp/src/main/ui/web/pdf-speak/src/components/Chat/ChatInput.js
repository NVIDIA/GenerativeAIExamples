import React, { useEffect, useRef, useState, useCallback } from "react";
import { IconArrowUp } from "@tabler/icons-react";
import MicButton from "../SpeechRecognition/MicButton";
import FileUploader from "../UploadContext/FileUploader";

const ChatInput = ({ onSend, setpdfContext, uploadedFile, setUploadedFile }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [fileUploaded, setIsFileUploaded] = useState(false);
  const [content, setContent] = useState("");
  const [placeholder, setPlaceholder] = useState("Chat with your PDF...");
  const [messageSent, setMessageSent] = useState(false);
  const textareaRef = useRef(null);
  const dropZoneRef = useRef(null);

  const handleFileUpload = (fileContent) => {
    console.log("Uploaded file content:", fileContent);
    setpdfContext(fileContent);
    setIsFileUploaded(true);
  };

  const handleChange = (e) => {
    const value = e.target.value;
    if (value.length > 4000) {
      alert("Message limit is 4000 characters");
      return;
    }

    setContent(value);
  };

  const handleTranscription = (transcribedText) => {
    setContent(transcribedText);
    if (!transcribedText) setPlaceholder("Chat with your PDF...");
  };

  const updatePlaceholder = (isListening) => {
    setPlaceholder(
      isListening ? "Speak to your PDF..." : "Chat with your PDF...",
    );
  };

  const handleSend = () => {
    if (!content) {
      alert("Please enter a message");
      return;
    }
    onSend({ role: "user", content });
    setContent("");
    setMessageSent(true);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.target === textareaRef.current) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.target === dropZoneRef.current) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0 && files[0].type === "application/pdf") {
      const reader = new FileReader();
      reader.onload = (event) => {
        const fileContent = event.target.result;
        handleFileUpload(fileContent);
      };
      reader.readAsText(files[0]);
    } else {
      alert("Please drop a PDF file.");
    }
  }, [handleFileUpload]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "inherit";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [content]);

  return (
    <div className="relative flex">
      <FileUploader onFileUpload={(file) => {
    setUploadedFile(file);
    handleFileUpload(file);
  }} 
  uploadedFile={uploadedFile}/>
      <div 
        className="relative flex-grow"
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {isDragging && (
          <div 
            ref={dropZoneRef}
            style={{width:"88%"}}
            className="absolute inset-0 flex items-center justify-center bg-blue-200 bg-opacity-75 z-10 rounded-lg border-2 border-blue-400 border-dashed"
          >
            <p className="text-lg font-bold text-blue-700">Drop your PDF here</p>
          </div>
        )}
        <textarea
          ref={textareaRef}
          style={{ resize: "none", width: "88%" }}
          className={`min-h-[44px] rounded-lg pl-4 pr-12 py-2 focus:outline-none focus:ring-1 focus:ring-neutral-300 border-2 border-neutral-200 ${!fileUploaded ? 'bg-gray-200 cursor-not-allowed' : ''}`}
          placeholder={fileUploaded ? placeholder : "Upload PDF to start chatting"}
          value={content}
          rows={1}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={!fileUploaded}
        />
      </div>

      <button onClick={handleSend} disabled={!fileUploaded}>
        <IconArrowUp className={`absolute right-2 bottom-1.5 h-8 w-8 rounded-full p-1 ${fileUploaded ? 'bg-blue-500 text-white hover:opacity-80 hover:cursor-pointer' : 'bg-gray-400 text-gray-600 cursor-not-allowed'}`} />
      </button>

      <MicButton
        onTranscription={handleTranscription}
        updatePlaceholder={updatePlaceholder}
        messageSent={messageSent}
        setMessageSent={setMessageSent}
        disabled={!fileUploaded}
      />
    </div>
  );
};

export default ChatInput;

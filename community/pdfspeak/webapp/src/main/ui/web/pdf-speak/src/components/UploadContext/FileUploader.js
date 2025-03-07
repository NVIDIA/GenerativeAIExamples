import React, { useEffect, useState, useCallback } from "react";
import axios from 'axios';
import {API_BASE_URL, API_ENDPOINTS} from '../../pages/APIConfig';
import LoadingProgress from "./LoadingProgress";

const FileUploader = ({ onFileUpload }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isFileUploaded, setIsFileUploaded] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) {
      alert("Please select a PDF file to upload.");
      return;
    }
    setSelectedFile(file);
  };

  const uploadFile = useCallback(async (file) => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.PDF_UPLOAD}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      console.log(response.data);
      onFileUpload(response.data);
      setIsFileUploaded(true);
      alert("File uploaded successfully!");
      
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Error uploading file. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [onFileUpload]);

  useEffect(() => {
    if (selectedFile && !isFileUploaded) {
      uploadFile(selectedFile);
    }
  }, [selectedFile, isFileUploaded, uploadFile]);

  return (
    <>
      <div className="flex items-center relative">
        <label
          htmlFor="file-input"
          className={`cursor-pointer px-1 py-2 rounded-md mr-2 text-white ${
            isFileUploaded
              ? "bg-green-500 hover:bg-green-600"
              : "bg-blue-500 hover:bg-blue-600"
          }`}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <img
            width="20"
            height="20"
            src={
              !isFileUploaded
                ? "https://img.icons8.com/?size=100&id=aNKH3E1vuPNc&format=png&color=000000"
                : "https://img.icons8.com/ios-filled/50/document--v1.png"
            }
            alt="external-paper-clip-glyph-website-ui-filled-agus-raharjo"
          />
        </label>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
          id="file-input"
        />
        {showTooltip && (
          <div className="absolute left-0 bottom-full mb-2 bg-gray-800 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
            {isFileUploaded
              ? `You are chatting with ${selectedFile.name}. Click to replace file.`
              : "Click to upload a PDF"}
          </div>
        )}
      </div>
      {isLoading && <LoadingProgress />}
    </>
  );
};


export default FileUploader;

import React, { useEffect, useState } from "react";

const LoadingProgress = () => {
    const [currentMessage, setCurrentMessage] = useState(0);
    const messages = [
      "Ingesting the PDF....",
      "Generating Metadata.....",
      "Analyzing Metadata.......",
      "Indexing PDF Chunks.....",
      "High performance VectorDB Ready...",
      "Almost there...."
    ];
  
    useEffect(() => {
      const interval = setInterval(() => {
        setCurrentMessage((prev) => (prev < messages.length - 1 ? prev + 1 : prev));
      }, 7000); 
  
      return () => clearInterval(interval);
    }, []);
  
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 mb-4">
              <iframe 
                src="https://lottie.host/embed/b7539aec-0c67-4f73-8fa0-c5594a0bb48c/O3oFcx1PY7.lottie"
                style={{ width: '100%', height: '100%' }}
              ></iframe>
            </div>
            <div className="text-center">
              <p className="text-gray-700 font-medium">{messages[currentMessage]}</p>
            </div>
            <div className="w-full mt-4 bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500"
                style={{ 
                  width: `${Math.min(((currentMessage + 1) / messages.length) * 100, 100)}%`
                }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    );
  };
  
export default LoadingProgress;
import React from "react";

const ChatMessage = ({ message }) => {
  const isAssistant = message.role === "assistant";

  const messageContainerStyle = {
    marginLeft: isAssistant ? "10px" : "auto",
    marginRight: isAssistant ? "auto" : "10px",
  };

  const renderContent = () => {
    if (isAssistant && message.content.includes("Download Highlighted References:")) { // Not really best practice. Will update next PR
      const parts = message.content.split(": ");
      const linkPart = parts[1].match(/\[(.*?)\]\((.*?)\)/);
      if (linkPart) {
        return (
          <>
            {parts[0]}: <a href={linkPart[2]} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">{linkPart[1]}</a>
          </>
        );
      }
    }
    return message.content;
  };

  return (
    <div className={`flex ${isAssistant ? "items-start" : "items-end"}`}>
      {isAssistant && (
        <img
          width="48"
          height="48"
          src="https://img.icons8.com/?size=100&id=115637&format=png&color=000000"
          alt="pdf"
          className="w-8 h-8 rounded-full mr-2"
        />
      )}
      <div
        className={`flex items-center ${
          isAssistant
            ? "bg-neutral-200 text-neutral-900"
            : "bg-blue-500 text-white"
        } rounded-2xl px-3 py-2 max-w-[67%] whitespace-pre-wrap`}
        style={{ ...messageContainerStyle, overflowWrap: "anywhere" }}
      >
        {renderContent()}
      </div>
      {!isAssistant && (
        <img
          src="https://img.icons8.com/color/48/circled-user-male-skin-type-7--v1.png"
          alt="User DP"
          className="w-8 h-8 rounded-full ml-2"
        />
      )}
    </div>
  );
};

export default ChatMessage;

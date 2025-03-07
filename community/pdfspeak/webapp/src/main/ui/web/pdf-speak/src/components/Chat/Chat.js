import React from "react";
import ChatInput from "./ChatInput";
import ChatLoader from "./ChatLoader";
import ChatMessage from "./ChatMessage";
import ResetChat from "./ResetChat";
import SpeakerButton from "./SpeakerButton";

const Chat = ({
  messages,
  loading,
  onSend,
  onReset,
  setpdfContext,
  uploadedFile,
  setUploadedFile,
  audioRef
}) => {
  
  return (
    <>
      <div className="flex flex-row justify-between items-center mb-4 sm:mb-8">
        <ResetChat onReset={onReset} />
        <SpeakerButton audioRef={audioRef} />
      </div>

      <div className="flex flex-col rounded-lg px-2 sm:p-4 sm:border border-neutral-300">
        {messages.map((message, index) => (
          <div key={index} className="my-1 sm:my-1.5">
            <ChatMessage message={message} />
          </div>
        ))}

        {loading && (
          <div className="my-1 sm:my-1.5">
            <ChatLoader />
          </div>
        )}

        <div className="mt-4 sm:mt-8 bottom-[56px] left-0 w-full">
          <ChatInput onSend={onSend} setpdfContext={setpdfContext} uploadedFile={uploadedFile}
  setUploadedFile={setUploadedFile}/>
        </div>
      </div>
    </>
  );
};

export default Chat;

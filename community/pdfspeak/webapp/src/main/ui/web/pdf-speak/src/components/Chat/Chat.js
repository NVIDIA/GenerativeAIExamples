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

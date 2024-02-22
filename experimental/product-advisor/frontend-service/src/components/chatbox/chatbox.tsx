// SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import { toast } from "react-toastify";

interface MessageData {
  role: string;
  content: string;
};


const Chatbox = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [newMessage, setNewMessage] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const toggleChatbox = async () => {
    setIsOpen(!isOpen);
  };

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const handleNewMessageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setNewMessage(event.target.value);
  };

  const handleReset = async () => {
    setMessages([]);
    addMessage('system', 'You are an advanced AI assistant helps customers on a Retail e-commerce website. You help answer questions for customers about products. Start the conversation by asking a couple of questions to clarify what the user is looking for. Use emojis but do not use too many. Structure your output using Markdown but do not use nested indentations.');
    await sleep(1000);
    addMessage('assistant', '');
    await sleep(1000);
    const introduction = "Hello! 👋 I'm your dedicated Shopping Advisor created by NVIDIA 🎮, here to answer any questions you might have and help you find anything you're looking for. What can I help you with today?";
    const words = introduction.split(' ');
    for (const word of words) {
      await sleep(40);
      updateLastMessage(word + " ");
    }

    try {
      const response = await fetch('http://127.0.0.1:5001/reset', {
        method: 'GET',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (err) {
      console.error(err);
    }

  }

  async function postData(url = '', data = {}) {
    // Default options are marked with *
    const response = await fetch(url, {
      method: 'POST',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data) // body data type must match "Content-Type" header
    });

    if (!response.ok) {
      // If the response is not ok, throw an error
      throw new Error(`HTTP error! status: ${response.status}`);
    } else {
      // If the response is ok, parse and return the response data
      return response.json();
    }
  }

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    const currentMessages = [...messages, { role: "user", "content": newMessage }];
    const filteredMessages = currentMessages.filter((message) => message.role === "user" || message.role === "assistant" || message.role === "system");

    addMessage("user", newMessage);
    addMessage('assistant', '');
    setNewMessage('');
    console.log('Filtered messages: ');
    console.log(filteredMessages);

    postData('http://127.0.0.1:5001/chat', filteredMessages)
      .then(data => {
        console.log(data); // JSON data parsed by `response.json()` call

        // Extract last message (response from assistant/LLM)
        updateLastMessage(data.messages[data.messages.length - 1].content);

        // Display products if they exist
        if (data.products && data.products.length !== 0) {
          console.log('We have images!');
          for (let i = 0; i < data.products.length; i++) {
            // Accessing the i-th element of each array
            const sum_ratings = data.products[i].ratings.reduce((acc: number, curr: number) => acc + curr, 0);
            const rating = sum_ratings / data.products[i].ratings.length;
            const ratingStr = rating.toFixed(2);
            addMessage('image', data.products[i].image + '|' + data.products[i].url + '|' + data.products[i].name + '|' + ratingStr);
          }
        }

        // Check if state of cart needs updated
        if (data.fn_metadata.fn_name && data.fn_metadata.fn_name === "add_to_cart") {
          toast.success("Successfully added " + String(data.fn_metadata.fn_args.quantity) + " unit(s) of " + data.fn_metadata.fn_args.name + " to your shopping cart!");
        } else if (data.fn_metadata.fn_name && data.fn_metadata.fn_name === "modify_item_in_cart") {
          toast.info("Updated shopping cart to have " + String(data.fn_metadata.fn_args.quantity) + " unit(s) of " + data.fn_metadata.fn_args.name + "!");
        } else if (data.fn_metadata.fn_name && data.fn_metadata.fn_name === "remove_from_cart") {
          toast.error("Removed " + data.fn_metadata.fn_args.name + " from your shopping cart!");
        }

      })
      .catch(error => {
        console.error('There was an error!', error);
      });
  };

  const handleKeyUp = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSendMessage();
    }
  };

  const addMessage = (role: string, content: string) => {
    setMessages(prevMessages => [...prevMessages, { role, content }]);
  };

  const updateLastMessage = (newContent: string) => {
    setMessages(prevMessages => {
      if (prevMessages.length === 0) return prevMessages;

      // Copy the array
      const updatedMessages = [...prevMessages];

      // Update the last message
      const lastMessageIndex = updatedMessages.length - 1;
      updatedMessages[lastMessageIndex] = {
        ...updatedMessages[lastMessageIndex],
        content: updatedMessages[lastMessageIndex].content + newContent
      };

      return updatedMessages;
    });
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="container">
      <div className="chatbox">
        <div className={`chatbox__support ${isOpen ? 'chatbox--active' : ''}`}>
          {/* Chatbox Header */}
          <div className="chatbox__header">
            {/* ... Header content ... */}
            <div className="chatbox__image--header">
              <img src="https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/02-nvidia-logo-color-blk-500x200-4c25-d.png" alt="image" height="72" />
            </div>
            <div className="chatbox__content--header">
              <h4 className="chatbox__heading--header">NVIDIA Retail Shopping Advisor</h4>
            </div>
          </div>

          {/* Chatbox Messages */}
          <div className="chatbox__messages">
            <div ref={messagesEndRef}></div>
            {[...messages].reverse().map((msg, index) => (
              <ChatMessage key={index} role={msg.role} content={msg.content} />
            ))}
          </div>

          {/* Chatbox Footer */}
          <div className="chatbox__footer">
            <input type="text" placeholder="Write a message..." value={newMessage} onChange={handleNewMessageChange} onKeyUp={handleKeyUp} />
            <button className="chatbox__send--footer send__button" onClick={handleSendMessage}>Send</button>
            <button className="chatbox__send--footer reset__button" onClick={handleReset}>Reset</button>
          </div>
        </div>

        {/* Chatbox Button */}
        <div className="chatbox__button">
          <button onClick={toggleChatbox}>
            {/* Button Image */}
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Chat_icon.svg/44px-Chat_icon.svg.png" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chatbox;
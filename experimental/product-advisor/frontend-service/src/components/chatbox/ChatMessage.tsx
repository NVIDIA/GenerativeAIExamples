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
import React from 'react';
import SafeHTML from './SafeHTML';
import Showdown from 'showdown';


interface MessageData {
  role: string
  content: string; // assuming message is a string that may contain HTML
}

const ChatMessage: React.FC<MessageData> = ({ role, content }) => {

  const classMap: Record<string, string> = {
    h1: 'messages__item--' + role + '--h1',
    h2: 'messages__item--' + role + '--h2',
    ul: 'messages__item--' + role + '--ul',
    li: 'messages__item--' + role + '--li',
    ol: 'messages__item--' + role + '--ol',
    p: 'messages__item--' + role + '--p'
  };

  type Binding = {
    type: string;
    regex: RegExp;
    replace: string;
  };

  const bindings: Binding[] = Object.keys(classMap).map((key) => ({
    type: 'output',
    regex: new RegExp(`<${key}(.*)>`, 'g'),
    replace: `<${key} class="${classMap[key]}" $1>`,
  }));

  const converter = new Showdown.Converter({
    extensions: [...bindings],
  });

  if (role !== "system") {
    if (role === "user") {
      return (
        <div className={`messages__item messages__item--${role}`}>
          {/* <SafeHTML html={content} /> */}
          <SafeHTML html={content} />
        </div>
      );
    } else if (role === "assistant") {
      return (
        <div className={`messages__item messages__item--${role}`}>
          {/* <SafeHTML html={content} /> */}
          <SafeHTML html={converter.makeHtml(content)} />
        </div>
      );
    } else if (role === "image") {
      const [image_path, url, product_name, product_rating] = content.split('|');
      if (image_path !== "" && url !== "" && product_name !== "" && product_rating !== "") {
        return (
          <div className={`messages__item messages__item--${role}`}>
            <img className="messages__item--image-img" src={image_path}></img>
            <div className="messages__item--image-box">
              <div>
                <a href={url}>{product_name}</a>
              </div>
              <div className="messages__item--image-stars">
                ⭐⭐⭐⭐⭐ {product_rating}
              </div>
            </div>
          </div>
        );
      }
    }
  }

  return null;
};

export default ChatMessage;
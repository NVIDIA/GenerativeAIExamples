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
import { IconDots } from "@tabler/icons-react"; // Ensure you have this library installed

const ChatLoader = () => {
  return (
    <div className="flex flex-col flex-start">
      <div
        className="flex items-center bg-neutral-200 text-neutral-900 rounded-2xl px-4 py-2 w-fit"
        style={{ overflowWrap: "anywhere" }}
      >
        <IconDots className="animate-pulse" />
      </div>
    </div>
  );
};

export default ChatLoader;

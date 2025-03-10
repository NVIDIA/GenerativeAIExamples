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

const ResetChat = ({ onReset }) => {
  return (
    <div className="flex flex-row items-center">
      <button
        className="text-white font-semibold rounded-lg px-4 py-2 bg-red-500 hover:bg-red-600 focus:outline-none focus:ring-1 focus:ring-red-500"
        onClick={() => onReset()}
      >
        Reset Chat
      </button>
    </div>
  );
};
export default ResetChat;

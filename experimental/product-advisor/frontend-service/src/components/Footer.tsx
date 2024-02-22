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
import React from "react";

const Footer = () => {
  return (
    <div className="bg-[#000000] h-24 mt-4 font-bold text-[28px] flex items-center justify-center text-white">
    <div className="bg-[#000000] h-18 mt-4 font-bold text-[28px] flex items-center justify-center text-white">
      {/* Categories */}
      <div className="bg-[#000000] mt-[1px] text-white px-3 py-2 lg:px-8 flex items-center gap-6">
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">CONTACT US</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">|</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">GUIDELINES & FAQ</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">|</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">PRIVACY POLICY</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">|</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">LOGOUT</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">|</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[12px] hover:underline">COPYRIGHT © NVIDIA CORPORATION</p>
        </div>
      </div>
      </div>
    </div>
  );
};

export default Footer;

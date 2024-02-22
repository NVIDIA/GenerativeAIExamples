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
import logo from "../assets/logo.png";
import { AiOutlineShoppingCart } from "react-icons/ai";

const Navbar = () => {
  return (
    <div className="">
      <div className="bg-[#000000] h-24 px-3 py-2 lg:px-5 text-white flex justify-between items-center">
        {/* Left */}
        <div className="flex  items-center gap-x-3 shrink-0">
          <div className="hover:bg-[#000000] p-2 rounded-full">
            <img src={logo} alt="" className=" h-14" />
          </div>
          <p className="text-[18px] font-bold">NVIDIA Gear Store</p>
        </div>
        {/* Right */}
        <div className="flex  items-center gap-x-2">
          <div className="flex items-center gap-2 hover:bg-[#000000] p-3 rounded-full">
            <p className="text-[12px] font-bold">Welcome!</p>
          </div>
        </div>
      </div>
      {/* Categories */}
      <div className="bg-[#5d5d5d] mt-[1px] text-white px-3 py-2 lg:px-8 flex items-center gap-6">
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">NVIDIA ELECTRONICS</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">APPAREL</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">BAGS</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">DRINKWARE</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">OFFICE</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">LIFESTYLE</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">LAST CALL!</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">DONATIONS</p>
        </div>
        <div className="flex items-center gap-1 hover:underline">
          <p className="text-[15px] hover:underline">ORDER STATUS</p>
        </div>
        <div className="hover:bg-[#000000] p-3 rounded-full">
            <AiOutlineShoppingCart className="w-6 h-6" />
          </div>
      </div>


    </div>
  );
};

export default Navbar;

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
import logo from '../../store/nvidia-logo-vert-rgb-blk-for-screen.png'
const Navbar = () => {
  return (
    <div className="flex h-[80px] sm:h-[90px] border-b border-neutral-300 py-4 px-4 sm:px-8 items-center relative">
      <iframe
        src="https://lottie.host/embed/241e7295-972d-4454-a566-aceb6bafd507/upNGWOM9DJ.lottie"
        width="60"
        height="60"
        allowFullScreen
        className="absolute left-4 top-1/2 transform -translate-y-1/2"
      ></iframe>

      <div className="font-bold text-4xl flex items-center ml-8">
        <a className="hover:opacity-50" href="#">
          &nbsp; PDFSpeak
        </a>
      </div>
      <img
        src={logo}
        alt="NVIDIA Logo"
        className="h-12 w-auto absolute right-4 top-1/2 transform -translate-y-1/2"
      />
    </div>
  );
};

export default Navbar;

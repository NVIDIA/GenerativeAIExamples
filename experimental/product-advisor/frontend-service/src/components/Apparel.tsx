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
import product from "../assets/NV00-0618-0619-Group_Full.jpg";


const Apparel = () => {
  return (
    <div className=" ">
      <div className="flex items-center md:w-max xl:w-[70vw] mx-auto gap-5">
        <div className="product-container">
          <img
            src={product}
            alt="MEN'S BEYOND YOGA TAKE IT EASY SHORTS"
            className="product-image"
          />
          <div className="product-details">
            <h1 className="title">MEN'S BEYOND YOGA TAKE IT EASY SHORTS</h1>
            <p className="price">$88.00</p>
            <br></br>
            <p className="description">
            Beyond Yoga Take It Easy shorts are total comfort whether you're lounging 
            on the couch or out and about for the day.  Available in Darkest Night or Olive Heather.
            <br></br>
            <br></br>
            Product Details:
            </p>
            <ul className="highlights">
              <li>Elasticized waistband, relaxed fit</li>
              <li>Two side hand pockets</li>
              <li>One zippered back pocket</li>
              <li>87% Polyester 13% Elastane</li>
              <li>4-way stretch</li>
              <li>7" inseam</li>
            </ul>
            <div className="purchase-info">
              <button>Add to Cart</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Apparel;

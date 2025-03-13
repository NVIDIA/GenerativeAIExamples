# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

![](images/EnvironmentDesign-HeaderImage.png)

# **Environment Design**


## **Demo Overview**

This workflow is using Generative AI to allow users to retexturize, relight any place objects into a new environment or the same one. Powered by NVIDIA Blackwell, this workflow accelerates design iterations with unparalleled speed and efficiency.


## **Key Points**



* Generate a specific material over a preselected object from an image - using CosXL for retexturing and SAM2 for accurate selections
* Reinforce texture/material onto object if necessary with IPAdapters using strong style transfer
* Relight the object in the same scene or a new designed space. Selected light colors and direction - Using IC- Relight and Stable Diffusion 1.5
* Upscale your final design to add extra detail - Using SAM ( Segment anything Models), In Context Lora, And Clip VIsion with Flux Redux, Flux Turbo and Flux Dev Fill. 

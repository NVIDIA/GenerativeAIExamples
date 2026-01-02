// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import { NextResponse, NextRequest } from "next/server";
import {
  createErrorResponse,
  validateRequiredFields,
} from "../utils/api-utils";
import { API_CONFIG, buildQueryUrl } from "@/app/config/api";

// GET /collections
export async function GET(request: NextRequest) {
  try {
    const url = buildQueryUrl(
      `${API_CONFIG.VDB.BASE_URL}${API_CONFIG.VDB.ENDPOINTS.COLLECTIONS.LIST}`,
      {}
    );

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch collections: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching collections:", error);
    return createErrorResponse(error);
  }
}

// POST /collections
export async function POST(request: NextRequest) {
  try {
    const { collection_names } = await request.json();

    const url = buildQueryUrl(
      `${API_CONFIG.VDB.BASE_URL}${API_CONFIG.VDB.ENDPOINTS.COLLECTIONS.CREATE}`,
      {}
    );

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(
        Array.isArray(collection_names) ? collection_names : [collection_names]
      ),
    });

    if (!response.ok) {
      throw new Error(`Failed to create collection: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error creating collection:", error);
    return createErrorResponse(error);
  }
}

// DELETE /collections
export async function DELETE(request: NextRequest) {
  try {
    const { collection_names } = await request.json();

    const url = buildQueryUrl(
      `${API_CONFIG.VDB.BASE_URL}${API_CONFIG.VDB.ENDPOINTS.COLLECTIONS.DELETE}`,
      {}
    );

    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(
        Array.isArray(collection_names) ? collection_names : [collection_names]
      ),
    });

    if (!response.ok) {
      throw new Error(`Failed to delete collection: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error deleting collection:", error);
    return createErrorResponse(error);
  }
}

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

import { NextRequest, NextResponse } from "next/server";
import { DocumentRequest, DocumentResponse } from "@/types/documents";
import {
  validateRequiredFields,
  APIError,
  createErrorResponse,
} from "../utils/api-utils";
import { API_CONFIG, buildQueryUrl } from "@/app/config/api";

export const config = {
  api: {
    bodyParser: false, // Disable the default body parser for file uploads
  },
};

// POST /documents - Upload new documents
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const documents = formData.getAll("documents") as File[];
    const dataStr = formData.get("data") as string;
    const metadata = JSON.parse(dataStr);

    // Create a new FormData instance for the upstream request
    const upstreamFormData = new FormData();

    // Add all documents to the upstream request
    documents.forEach((file) => {
      upstreamFormData.append("documents", file);
    });

    // Add metadata
    upstreamFormData.append("data", dataStr);

    // Forward the request to the VDB service
    const url = `${API_CONFIG.VDB.BASE_URL}${API_CONFIG.VDB.ENDPOINTS.DOCUMENTS.UPLOAD}`;

    const response = await fetch(url, {
      method: "POST",
      body: upstreamFormData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to upload documents");
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error uploading documents:", error);
    return createErrorResponse(error);
  }
}

// PATCH /documents - Update documents
export async function PATCH(request: NextRequest) {
  try {
    const body: DocumentRequest = await request.json();

    try {
      validateRequiredFields(body, ["collection_name", "documents"]);
      if (body.documents.length === 0) {
        throw new APIError("Documents array cannot be empty", 400);
      }
    } catch (error) {
      return createErrorResponse(error);
    }

    // TODO: Implement actual document update logic
    const updatedDocuments: DocumentResponse[] = body.documents.map(
      (doc, index) => ({
        document_id: `doc${index}`,
        document_name: doc.document_name,
        size_bytes: Math.floor(Math.random() * 1000000),
        timestamp: new Date().toISOString(),
      })
    );

    return NextResponse.json({
      message: "Documents updated successfully",
      total_documents: updatedDocuments.length,
      updated_documents: updatedDocuments,
    });
  } catch (error) {
    console.error("Error updating documents:", error);
    return NextResponse.json(
      { error: "Failed to update documents" },
      { status: 500 }
    );
  }
}

// GET /documents - List documents
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const collection_name = searchParams.get("collection_name");

    if (!collection_name) {
      throw new APIError("collection_name is required", 400);
    }

    const url = buildQueryUrl(
      `${API_CONFIG.VDB.BASE_URL}${API_CONFIG.VDB.ENDPOINTS.DOCUMENTS.LIST}`,
      { collection_name }
    );

    const response = await fetch(url);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to fetch documents");
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching documents:", error);
    return createErrorResponse(error);
  }
}

// DELETE /documents - Delete documents
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const collection_name = searchParams.get("collection_name");

    if (!collection_name) {
      throw new APIError("collection_name is required", 400);
    }

    const body = await request.json();
    const document_names = Array.isArray(body) ? body : [];

    const url = buildQueryUrl(
      `${API_CONFIG.VDB.BASE_URL}${API_CONFIG.VDB.ENDPOINTS.DOCUMENTS.DELETE}`,
      { collection_name }
    );

    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(document_names),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to delete documents");
    }

    const data = await response.json();
    console.log("Documents deleted:", data);

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error deleting documents:", error);
    return createErrorResponse(error);
  }
}

// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { NextRequest } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_CHAT_BASE_URL ?? "http://localhost:8081/v1";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    console.log("Frontend API route received:", {
      vm_ip: body.vm_ip,
      username: body.username,
      configuration_keys: Object.keys(body.configuration || {}),
      full_configuration: body.configuration
    });
    
    // Forward the request to the backend
    const response = await fetch(`${API_BASE_URL}/apply-configuration`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      return new Response(error, { status: response.status });
    }

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error) {
    console.error("Error applying configuration:", error);
    return new Response(
      JSON.stringify({ error: "Failed to apply configuration" }),
      { status: 500 }
    );
  }
} 
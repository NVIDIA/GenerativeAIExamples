// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Use the same base URL as the chat API
    const baseUrl = process.env.NEXT_PUBLIC_CHAT_BASE_URL || 'http://localhost:8081/v1';
    const backendUrl = `${baseUrl}/available-models`;
    
    console.log('[API] Fetching models from:', backendUrl);
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      console.error('[API] Backend returned error:', response.status);
      return NextResponse.json(
        { error: 'Failed to fetch models', models: [] },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('[API] Successfully fetched', data.models?.length || 0, 'models');
    return NextResponse.json(data);
  } catch (error) {
    console.error('[API] Error fetching available models:', error);
    return NextResponse.json(
      { error: 'Failed to fetch models', models: [] },
      { status: 500 }
    );
  }
}

export const dynamic = 'force-dynamic';


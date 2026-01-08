/**
 * Test Configuration API Route
 * 
 * This route tests a recommended vGPU configuration locally by:
 * 1. Running a Docker container with vLLM
 * 2. Monitoring GPU/compute usage
 * 3. Reporting if the configuration is viable
 */

import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 600; // 10 minutes for testing
export const dynamic = 'force-dynamic';

interface TestConfigurationRequest {
  deployment_mode?: string;
  hf_token?: string;
  model_tag?: string;
  configuration: {
    vgpu_profile?: string;
    gpu_memory_size?: number;
    max_kv_tokens?: number;
    vcpu_count?: number;
    system_RAM?: number;
    model_tag?: string;
    model_name?: string;
    parameters?: {
      model_tag?: string;
      model_name?: string;
      [key: string]: any;
    };
    [key: string]: any;
  };
  test_duration_seconds?: number;
}

export async function POST(request: NextRequest) {
  try {
    const body: TestConfigurationRequest = await request.json();
    
    const {
      deployment_mode = 'local',
      hf_token,
      configuration,
      test_duration_seconds = 30
    } = body;

    console.log("Received test-configuration request (local):", {
      vgpu_profile: configuration?.vgpu_profile
    });

    // Extract model from various possible locations in the configuration
    const model_tag = body.model_tag || 
                     configuration?.model_tag || 
                     configuration?.model_name ||
                     configuration?.parameters?.model_tag ||
                     configuration?.parameters?.model_name ||
                     'Qwen/Qwen2.5-0.5B-Instruct';  // Default to an open-access model

    console.log("🔍 API Route Model Selection:");
    console.log("  - body.model_tag:", body.model_tag);
    console.log("  - configuration?.model_tag:", configuration?.model_tag);
    console.log("  - configuration?.model_name:", configuration?.model_name);
    console.log("  - configuration?.parameters?.model_tag:", configuration?.parameters?.model_tag);
    console.log("  - configuration?.parameters?.model_name:", configuration?.parameters?.model_name);
    console.log("  - Final model_tag:", model_tag);

    // Build backend request payload (always local)
    const backendPayload: any = {
      deployment_mode: 'local',
      hf_token,
      model_tag,
      configuration,
      test_duration_seconds
    };

    // Forward to Python backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8081';
    const backendResponse = await fetch(`${backendUrl}/test-configuration`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendPayload),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({ error: 'Unknown error' }));
      return NextResponse.json(
        { error: errorData.error || `Backend returned status ${backendResponse.status}` },
        { status: backendResponse.status }
      );
    }

    // Stream the response from backend to frontend
    return new Response(backendResponse.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });

  } catch (error: any) {
    console.error("Error in test-configuration route:", error);
    return NextResponse.json(
      { error: error.message || "Failed to process request" },
      { status: 500 }
    );
  }
}
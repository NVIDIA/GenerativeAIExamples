/**
 * Apply Configuration API Route
 * 
 * This route applies a vGPU configuration by deploying vLLM locally using Docker.
 */

import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 600; // 10 minutes for deployment
export const dynamic = 'force-dynamic';

interface ApplyConfigurationRequest {
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
  description?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: ApplyConfigurationRequest = await request.json();
    
    const {
      hf_token,
      configuration,
      description
    } = body;

    console.log("🚀 Received apply-configuration request (local deployment):", {
      vgpu_profile: configuration?.vgpu_profile || configuration?.vGPU_profile
    });

    // HuggingFace token is required
    if (!hf_token) {
      return NextResponse.json(
        { error: "Hugging Face token is required" },
        { status: 400 }
      );
    }

    // Extract model from various possible locations in the configuration
    const model_tag = body.model_tag || 
                     configuration?.model_tag || 
                     configuration?.model_name ||
                     configuration?.parameters?.model_tag ||
                     configuration?.parameters?.model_name ||
                     'meta-llama/Meta-Llama-3-8B-Instruct';

    // Build backend request payload (always local)
    const backendPayload: any = {
      deployment_mode: 'local',
      hf_token,
      model_tag,
      configuration,
      description: description || 'Local deployment via vGPU Sizing Advisor'
    };

    // Forward to Python backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8081';
    const backendResponse = await fetch(`${backendUrl}/v1/apply-configuration`, {
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
    console.error("Error in apply-configuration route:", error);
    
    // Check if it's a network error (backend not responding)
    let errorMsg = "Failed to process request";
    if (error.code === 'ECONNREFUSED' || error.message?.includes('ECONNREFUSED') || error.message?.includes('fetch failed')) {
      errorMsg = "Backend is not responding or is not running. Please ensure the backend server is started.";
    } else if (error.message) {
      errorMsg = error.message;
    }
    
    return NextResponse.json(
      { error: errorMsg },
      { status: 500 }
    );
  }
}


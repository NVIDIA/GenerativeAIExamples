/**
 * Test Configuration API Route
 * 
 * This route tests a recommended vGPU configuration on a VM by:
 * 1. SSH into the VM
 * 2. Running a lightweight test container/workload
 * 3. Monitoring GPU/compute usage
 * 4. Reporting if the configuration is viable
 */

import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 600; // 10 minutes for testing
export const dynamic = 'force-dynamic';

interface TestConfigurationRequest {
  deployment_mode?: string;
  vm_ip?: string;
  username?: string;
  password?: string;
  ssh_port?: number;
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
      deployment_mode = 'remote',
      vm_ip,
      username,
      password,
      ssh_port = 22,
      hf_token,
      configuration,
      test_duration_seconds = 30
    } = body;

    console.log("🧪 Received test-configuration request:", {
      deployment_mode,
      vm_ip: deployment_mode === 'remote' ? vm_ip : 'local',
      username: deployment_mode === 'remote' ? username : 'local',
      vgpu_profile: configuration?.vgpu_profile
    });

    // Only validate VM fields for remote deployment
    if (deployment_mode === 'remote') {
      if (!vm_ip) {
        return NextResponse.json(
          { error: "vm_ip is required for remote deployment" },
          { status: 400 }
        );
      }

      if (!username || !password) {
        return NextResponse.json(
          { error: "username and password are required for remote deployment" },
          { status: 400 }
        );
      }
    }

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

    // Build backend request payload
    const backendPayload: any = {
      deployment_mode,
      hf_token,
      model_tag,
      configuration,
      test_duration_seconds
    };

    // Only include VM fields for remote deployment
    if (deployment_mode === 'remote') {
      backendPayload.vm_ip = vm_ip;
      backendPayload.ssh_port = ssh_port;
      backendPayload.username = username;
      backendPayload.password = password;
    }

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


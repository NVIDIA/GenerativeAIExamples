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
  vm_ip: string;
  username: string;
  password: string;
  ssh_port?: number;
  hf_token?: string;
  model_tag?: string;
  configuration: {
    vgpu_profile: string;
    gpu_memory_size?: number;
    max_kv_tokens?: number;
    vcpu_count?: number;
    system_RAM?: number;
    model_tag?: string;
  };
  test_duration_seconds?: number;
}

export async function POST(request: NextRequest) {
  try {
    const body: TestConfigurationRequest = await request.json();
    
    console.log("🧪 Received test-configuration request:", {
      vm_ip: body.vm_ip,
      username: body.username,
      vgpu_profile: body.configuration?.vgpu_profile
    });

    const {
      vm_ip,
      username,
      password,
      ssh_port = 22,
      hf_token,
      configuration,
      test_duration_seconds = 30
    } = body;

    if (!vm_ip) {
      return NextResponse.json(
        { error: "vm_ip is required" },
        { status: 400 }
      );
    }

    if (!username || !password) {
      return NextResponse.json(
        { error: "username and password are required" },
        { status: 400 }
      );
    }

    if (!configuration?.vgpu_profile) {
      return NextResponse.json(
        { error: "configuration.vgpu_profile is required" },
        { status: 400 }
      );
    }

    const model_tag = body.model_tag || configuration.model_tag || 'meta-llama/Llama-3.2-1B';

    // Forward to Python backend for SSH-based testing
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8081';
    const backendResponse = await fetch(`${backendUrl}/test-configuration`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        vm_ip,
        ssh_port,
        username,
        password,
        hf_token,
        model_tag,
        configuration,
        test_duration_seconds
      }),
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


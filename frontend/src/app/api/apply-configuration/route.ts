/**
 * Apply Configuration API Route (gRPC version)
 * 
 * This route uses gRPC to directly communicate with the vLLM gRPC server
 * running on the target VM, bypassing the Python backend entirely.
 */

import { NextRequest, NextResponse } from "next/server";
import { VLLMGrpcClient, streamToAsyncIterator } from "@/lib/vllmGrpcClient";

export const maxDuration = 1800; // 30 minutes
export const dynamic = 'force-dynamic';

interface ConfigurationRequest {
  vm_ip: string;
  grpc_port?: number;
  ssh_port?: number;
  username?: string;
  password?: string;
  hf_token?: string;
  model_tag?: string;
  configuration: {
    gpu_memory_size?: number;
    max_kv_tokens?: number;
    vgpu_profile?: string;
    vcpu_count?: number;
    system_RAM?: number;
    model_tag?: string;
  };
}

export async function POST(request: NextRequest) {
  const encoder = new TextEncoder();
  let client: VLLMGrpcClient | null = null;

  try {
    const body: ConfigurationRequest = await request.json();
    
    console.log("📥 Received apply-configuration request:", {
      vm_ip: body.vm_ip,
      model: body.model_tag,
      grpc_port: body.grpc_port || 50051
    });

    const {
      vm_ip,
      grpc_port = 50051,
      hf_token,
      model_tag: model_tag_direct,
      configuration = {}
    } = body;

    // Extract model_tag from either direct parameter or configuration
    const model_tag = model_tag_direct || configuration.model_tag;

    if (!vm_ip) {
      return NextResponse.json(
        { error: "vm_ip is required" },
        { status: 400 }
      );
    }

    if (!model_tag) {
      return NextResponse.json(
        { error: "model_tag is required (either as direct parameter or in configuration)" },
        { status: 400 }
      );
    }

    // Create streaming response
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // Step 1: Connect to gRPC server
          const sendProgress = (message: string, step: number = 1) => {
            const data = JSON.stringify({
              status: "executing",
              message,
              current_step: step,
              total_steps: 6,
              display_message: message
            });
            controller.enqueue(encoder.encode(`data: ${data}\n\n`));
          };

          const sendError = (message: string, error: string) => {
            const data = JSON.stringify({
              status: "error",
              message,
              error
            });
            controller.enqueue(encoder.encode(`data: ${data}\n\n`));
          };

          const sendSuccess = (message: string) => {
            const data = JSON.stringify({
              status: "success",
              message
            });
            controller.enqueue(encoder.encode(`data: ${data}\n\n`));
          };

          sendProgress(`$ Starting configuration process...`, 1);
          sendProgress(`$ Connecting to ${vm_ip}:${grpc_port}...`, 1);

          // Initialize gRPC client
          client = new VLLMGrpcClient(vm_ip, grpc_port);
          
          try {
            await client.connect();
            sendProgress(`$ Connected successfully to gRPC server`, 1);
          } catch (connectError: any) {
            sendError(
              "Failed to connect to VM",
              `Could not connect to gRPC server at ${vm_ip}:${grpc_port}. ` +
              `Please ensure the vLLM gRPC server is running on the VM. ` +
              `Error: ${connectError.message}`
            );
            controller.close();
            return;
          }

          // Step 2: Get system information
          sendProgress(`$ Gathering system information...`, 2);
          
          try {
            const sysInfo = await client.getSystemInfo();
            const gpuInfo = await client.getGPUInfo();
            
            sendProgress(
              `$ Hypervisor Layer: ${sysInfo.hypervisor}, OS: ${sysInfo.os.split(' ')[0]}`,
              2
            );
            sendProgress(`$ Checking GPU availability...`, 2);
            sendProgress(
              `$ GPU: ${gpuInfo.gpu_name} (${gpuInfo.gpu_memory_free_mb}MB / ${gpuInfo.gpu_memory_total_mb}MB free)`,
              2
            );
          } catch (infoError: any) {
            sendError("Failed to get system information", infoError.message);
            controller.close();
            return;
          }

          // Step 3: Setup environment
          sendProgress(`$ Starting setup phase...`, 3);
          sendProgress(`$ Setting up Python environment...`, 3);
          
          try {
            const setupStream = client.setupEnvironment();
            for await (const update of streamToAsyncIterator(setupStream)) {
              if (update.status === 'error') {
                sendError("Environment setup failed", update.error);
                controller.close();
                return;
              }
              sendProgress(`$ ${update.message}`, 3);
            }
          } catch (setupError: any) {
            sendError("Environment setup failed", setupError.message);
            controller.close();
            return;
          }

          // Step 4: Authenticate with HuggingFace (if token provided)
          if (hf_token) {
            sendProgress(`$ Authenticating with HuggingFace...`, 4);
            
            try {
              const authResult = await client.authenticateHuggingFace(hf_token);
              if (authResult.status === 'error') {
                sendError("HuggingFace authentication failed", authResult.error);
                controller.close();
                return;
              }
              sendProgress(`$ HuggingFace authentication successful`, 4);
            } catch (authError: any) {
              sendError("HuggingFace authentication failed", authError.message);
              controller.close();
              return;
            }
          } else {
            sendProgress(`$ Skipping HuggingFace authentication (no token provided)`, 4);
          }

          // Step 5: Install vLLM (if needed)
          sendProgress(`$ Installing vLLM (this may take several minutes)...`, 5);
          
          try {
            const installStream = client.installVLLM();
            for await (const update of streamToAsyncIterator(installStream)) {
              if (update.status === 'error') {
                sendError("vLLM installation failed", update.error);
                controller.close();
                return;
              }
              sendProgress(`$ ${update.message}`, 5);
            }
          } catch (installError: any) {
            sendError("vLLM installation failed", installError.message);
            controller.close();
            return;
          }

          // Step 6: Start vLLM server
          sendProgress(`$ Starting vLLM server with model ${model_tag}...`, 6);
          
          // Calculate parameters from configuration
          const gpuMemUtil = configuration.gpu_memory_size && configuration.vgpu_profile
            ? Math.min(0.85, configuration.gpu_memory_size / parseInt(configuration.vgpu_profile.match(/\d+/)?.[0] || "24"))
            : 0.85;
          
          const maxModelLen = configuration.max_kv_tokens || 2048;

          try {
            const startStream = client.startVLLM({
              model_name: model_tag,
              gpu_memory_utilization: gpuMemUtil,
              max_model_len: maxModelLen,
              max_num_seqs: 1,
              dtype: "float16",
              port: 8000,
              trust_remote_code: true
            });

            for await (const update of streamToAsyncIterator(startStream)) {
              if (update.status === 'error') {
                sendError("vLLM startup failed", update.error);
                controller.close();
                return;
              }
              
              if (update.status === 'success') {
                sendSuccess(update.message);
                sendProgress(
                  `$ ✅ Deployment complete! vLLM API: http://${vm_ip}:8000`,
                  6
                );
              } else {
                sendProgress(`$ ${update.message}`, 6);
              }
            }
          } catch (startError: any) {
            sendError("vLLM startup failed", startError.message);
            controller.close();
            return;
          }

          // Close the stream
          controller.close();

        } catch (error: any) {
          console.error("Error in apply-configuration:", error);
          const data = JSON.stringify({
            status: "error",
            message: "Configuration failed",
            error: error.message || "Unknown error occurred"
          });
          controller.enqueue(encoder.encode(`data: ${data}\n\n`));
          controller.close();
        } finally {
          // Clean up gRPC client
          if (client) {
            client.close();
          }
        }
      }
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });

  } catch (error: any) {
    console.error("Error in apply-configuration route:", error);
    return NextResponse.json(
      { error: error.message || "Failed to process request" },
      { status: 500 }
    );
  }
}

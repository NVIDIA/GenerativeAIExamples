// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const source = searchParams.get('source');

    if (!source) {
      return NextResponse.json(
        { error: 'Source parameter is required' },
        { status: 400 }
      );
    }

    console.log(`📥 Download request for: ${source}`);

    // Security: Only allow downloading from vgpu_docs directory
    const fileName = path.basename(source);
    const vgpuDocsPath = path.join(process.cwd(), '..', 'vgpu_docs');
    const filePath = path.join(vgpuDocsPath, fileName);

    // Verify the file exists and is within vgpu_docs
    const normalizedPath = path.normalize(filePath);
    const normalizedDocsPath = path.normalize(vgpuDocsPath);
    
    if (!normalizedPath.startsWith(normalizedDocsPath)) {
      console.error('❌ Security violation: Attempted path traversal');
      return NextResponse.json(
        { error: 'Invalid file path' },
        { status: 403 }
      );
    }

    if (!fs.existsSync(filePath)) {
      console.error(`❌ File not found: ${filePath}`);
      return NextResponse.json(
        { error: 'File not found' },
        { status: 404 }
      );
    }

    // Read the file
    const fileBuffer = fs.readFileSync(filePath);
    
    console.log(`✅ Serving PDF: ${fileName} (${fileBuffer.length} bytes)`);

    // Return the file with appropriate headers
    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${fileName}"`,
        'Content-Length': fileBuffer.length.toString(),
      },
    });
  } catch (error) {
    console.error('Error serving PDF:', error);
    return NextResponse.json(
      { error: 'Failed to download file' },
      { status: 500 }
    );
  }
}


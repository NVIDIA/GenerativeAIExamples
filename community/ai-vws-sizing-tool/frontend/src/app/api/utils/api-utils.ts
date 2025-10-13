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

import { NextResponse } from "next/server";
import { BaseResponse } from "@/types/common";

export class APIError extends Error {
  constructor(
    public message: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = "APIError";
  }
}

export function createSuccessResponse<T extends BaseResponse>(
  data: T,
  status: number = 200
) {
  return NextResponse.json(data, { status });
}

export function createErrorResponse(error: unknown) {
  if (error instanceof APIError) {
    return NextResponse.json(
      { error: error.message, details: error.details },
      { status: error.statusCode }
    );
  }

  console.error("Unhandled error:", error);
  return NextResponse.json({ error: "Internal server error" }, { status: 500 });
}

export function validateRequiredFields(obj: any, fields: string[]) {
  const missingFields = fields.filter((field) => !obj[field]);
  if (missingFields.length > 0) {
    throw new APIError(
      `Missing required fields: ${missingFields.join(", ")}`,
      400
    );
  }
}

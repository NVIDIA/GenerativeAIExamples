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

"use client";
import Image from "next/image";

interface SourceItemProps {
  name: string;
  onDelete: () => void;
}

export default function SourceItem({ name, onDelete }: SourceItemProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete();
  };

  return (
    <div className="group flex cursor-pointer items-center justify-between border-b border-neutral-800 px-3 py-2 hover:bg-neutral-900">
      <div className="flex min-w-0 flex-1 items-center gap-2 overflow-hidden">
        <Image
          src="/document.svg"
          alt="Document"
          width={16}
          height={16}
          className="flex-shrink-0"
        />
        <span
          className="max-w-[180px] truncate text-sm text-white"
          title={name}
        >
          {name}
        </span>
      </div>
      <button
        onClick={handleDelete}
        className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-gray-400 hover:bg-neutral-800 hover:text-red-500"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 6h18" />
          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
        </svg>
      </button>
    </div>
  );
}

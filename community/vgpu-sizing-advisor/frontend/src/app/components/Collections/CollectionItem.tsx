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

import { useState, useEffect } from "react";
import AddSourceModal from "./AddSourceModal";

import Image from "next/image";

interface CollectionItemProps {
  name: string;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  handleViewFiles: (name: string) => void;
  onDocumentsUpdate: () => void;
}

export default function CollectionItem({
  name,
  isSelected,
  onSelect,
  onDelete,
  handleViewFiles,
  onDocumentsUpdate,
}: CollectionItemProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isAddSourceModalOpen, setIsAddSourceModalOpen] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState({
    top: 0,
    right: 0,
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (isDropdownOpen && !target.closest(".dropdown-container")) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener("click", handleClickOutside);
    }

    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  }, [isDropdownOpen]);

  const handleDropdownClick = (e: React.MouseEvent) => {
    e.stopPropagation();

    // Calculate and set the dropdown position based on the button position
    if (e.currentTarget) {
      const button = e.currentTarget as HTMLElement;
      const rect = button.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY,
        right: window.innerWidth - rect.right - window.scrollX,
      });
    }

    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleAddSource = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDropdownOpen(false);
    setIsAddSourceModalOpen(true);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDropdownOpen(false);
    onDelete();
  };

  return (
    <div
      className="group relative flex cursor-pointer items-center justify-between border-b border-neutral-800 px-3 py-2 hover:bg-neutral-900"
      onClick={onSelect}
    >
      <div className="flex min-w-0 flex-1 items-center gap-2 overflow-hidden">
        <div
          className={`mr-2 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full border ${isSelected ? "border-[var(--nv-green)] bg-[var(--nv-green)]" : "border-gray-600"}`}
        >
          {isSelected && <div className="h-2 w-2 rounded-full bg-black" />}
        </div>
        <Image
          src="/collection.svg"
          alt="NVIDIA Logo"
          width={20}
          height={20}
          className="flex-shrink-0 invert"
        />
        <span
          className="max-w-[180px] truncate text-sm text-white"
          title={name}
        >
          {name}
        </span>
      </div>

      <button
        onClick={handleDropdownClick}
        className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-gray-400 hover:bg-neutral-800 hover:text-white"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <circle cx="12" cy="12" r="2" />
          <circle cx="12" cy="5" r="2" />
          <circle cx="12" cy="19" r="2" />
        </svg>
      </button>

      {isDropdownOpen && (
        <div
          className="dropdown-container fixed z-50 w-48"
          style={{
            top: `${dropdownPosition.top}px`,
            right: `${dropdownPosition.right}px`,
          }}
        >
          <div className="rounded-md border border-neutral-800 bg-neutral-900 shadow-lg">
            <button
              onClick={handleAddSource}
              className="flex w-full items-center px-4 py-2 text-sm text-white hover:bg-neutral-800"
            >
              Add Source
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsDropdownOpen(false);
                handleViewFiles(name);
              }}
              className="flex w-full items-center px-4 py-2 text-sm text-white hover:bg-neutral-800"
            >
              View Files
            </button>
            <button
              onClick={handleDelete}
              className="flex w-full items-center px-4 py-2 text-sm text-red-500 hover:bg-neutral-800"
            >
              Delete Collection
            </button>
          </div>
        </div>
      )}

      <AddSourceModal
        isOpen={isAddSourceModalOpen}
        onClose={() => setIsAddSourceModalOpen(false)}
        collectionName={name}
        onDocumentsUpdate={onDocumentsUpdate}
      />
    </div>
  );
}

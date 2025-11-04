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

import { useState } from "react";
import { useApp } from "@/app/context/AppContext";
import Modal from "../Modal/Modal";

interface NewCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function NewCollectionModal({
  isOpen,
  onClose,
}: NewCollectionModalProps) {
  const { setCollections } = useApp();
  const [collectionName, setCollectionName] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (files: File[]) => {
    setSelectedFiles((prev) => [...prev, ...files]);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleCollectionNameChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setCollectionName(e.target.value.replace(/\s+/g, "_"));
  };

  const handleReset = () => {
    setCollectionName("");
    setSelectedFiles([]);
    setError(null);
  };

  const handleSubmit = async () => {
    try {
      // 1. Validate collection name format and constraints
      if (!collectionName.match(/^[a-zA-Z_][a-zA-Z0-9_]*$/)) {
        setError(
          "Collection name must start with a letter or underscore and can only contain letters, numbers and underscores"
        );
        return;
      }

      // 2. Check if collection already exists
      const checkResponse = await fetch("/api/collections");
      if (!checkResponse.ok) {
        throw new Error("Failed to check existing collections");
      }
      const { collections: existingCollections } = await checkResponse.json();
      if (
        existingCollections.some(
          (c: any) => c.collection_name === collectionName
        )
      ) {
        setError("A collection with this name already exists");
        return;
      }

      setIsLoading(true);
      setError(null);

      // 3. Create the new collection
      const createCollectionResponse = await fetch("/api/collections", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          collection_names: [collectionName],
        }),
      });

      if (!createCollectionResponse.ok) {
        throw new Error("Failed to create collection");
      }

      const collectionData = await createCollectionResponse.json();

      // Check if collection creation failed
      if (collectionData.failed?.length > 0) {
        throw new Error(
          `Failed to create collection: ${collectionData.message || "Unknown error"}`
        );
      }

      // 4. Upload documents to the collection (if files are provided)
      if (selectedFiles.length > 0) {
        const formData = new FormData();
        selectedFiles.forEach((file) => {
          formData.append("documents", file);
        });

        // Add metadata as a JSON string
        const metadata = {
          collection_name: collectionName,
        };
        formData.append("data", JSON.stringify(metadata));

        const uploadResponse = await fetch("/api/documents", {
          method: "POST",
          body: formData,
        });

        if (!uploadResponse.ok) {
          throw new Error("Failed to upload documents");
        }
      }

      // 5. Update the collections list in the UI
      const getCollectionsResponse = await fetch("/api/collections");
      if (!getCollectionsResponse.ok) {
        throw new Error("Failed to fetch updated collections");
      }

      const { collections } = await getCollectionsResponse.json();
      setCollections(
        collections.map((collection: any) => ({
          collection_name: collection.collection_name,
          document_count: collection.num_entities,
          index_count: collection.num_entities,
        }))
      );

      // 6. Close the modal and reset state
      onClose();
      setCollectionName("");
      setSelectedFiles([]);
    } catch (err) {
      console.error("Error creating collection:", err);
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const modalDescription =
    "Upload a collection of source files to provide the model with relevant information for more tailored responses (e.g., marketing plans, research notes, meeting transcripts, sales documents).";

  const collectionNameInput = (
    <div className="mb-4">
      <label className="mb-2 block text-sm font-medium">Collection Name</label>
      <input
        type="text"
        value={collectionName}
        onChange={handleCollectionNameChange}
        placeholder="Enter collection name"
        className="w-full rounded-md bg-neutral-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--nv-green)]"
        disabled={isLoading}
      />
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="New Collection"
      description={modalDescription}
      isLoading={isLoading}
      error={error}
      selectedFiles={selectedFiles}
      submitButtonText="Create Collection"
      isSubmitDisabled={!collectionName}
      onFileSelect={handleFileSelect}
      onRemoveFile={removeFile}
      onReset={handleReset}
      onSubmit={handleSubmit}
      fileInputId="fileInput"
      customContent={collectionNameInput}
    />
  );
}

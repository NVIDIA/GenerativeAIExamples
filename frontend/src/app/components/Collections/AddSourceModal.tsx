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
import { useApp } from "../../context/AppContext";
import Modal from "../Modal/Modal";

interface AddSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  collectionName: string;
  onDocumentsUpdate: () => void;
}

export default function AddSourceModal({
  isOpen,
  onClose,
  collectionName,
  onDocumentsUpdate,
}: AddSourceModalProps) {
  const { collections, setCollections } = useApp();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedCollection, setSelectedCollection] = useState(collectionName);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedCollection(collectionName);
  }, [collectionName]);

  // Function to fetch existing documents and check for duplicates
  const checkForDuplicates = async (files: File[], collection: string) => {
    try {
      const response = await fetch(
        `/api/documents?collection_name=${encodeURIComponent(collection)}`
      );

      if (!response.ok) {
        if (response.status === 400) {
          console.error("Bad request when checking for duplicates");
          return [];
        }
        throw new Error(`Error fetching documents: ${response.status}`);
      }

      const data = await response.json();

      // Extract document_name values from documents
      const existingFiles = data.documents
        .map((doc: any) => doc.document_name || null)
        .filter(Boolean);

      // Find duplicates by comparing file names with document_name values
      const duplicates = files.filter((file) =>
        existingFiles.includes(file.name)
      );

      return duplicates;
    } catch (err) {
      console.error("Error checking for duplicate files:", err);
      return [];
    }
  };

  const handleFileSelect = (files: File[]) => {
    setSelectedFiles((prev) => [...prev, ...files]);
    setError(null);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
    setError(null);
  };

  const handleReset = () => {
    setSelectedCollection(collectionName);
    setSelectedFiles([]);
    setError(null);
  };

  const handleSubmit = async () => {
    try {
      // 1. Check for duplicate files in the collection
      const duplicates = await checkForDuplicates(
        selectedFiles,
        selectedCollection
      );

      if (duplicates.length > 0) {
        const duplicateNames = duplicates.map((file) => file.name).join(", ");
        setError(
          `The following files already exist in this collection: ${duplicateNames}`
        );
        return;
      }

      setIsLoading(true);
      setError(null);

      // 2. Prepare and upload documents to the collection
      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append("documents", file);
      });

      // Add metadata as JSON string
      const metadata = {
        collection_name: selectedCollection,
      };
      formData.append("data", JSON.stringify(metadata));

      const uploadResponse = await fetch("/api/documents", {
        method: "POST",
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error("Failed to upload documents");
      }

      // 3. Update the collections list in the UI
      const getCollectionsResponse = await fetch("/api/collections");
      if (!getCollectionsResponse.ok) {
        throw new Error("Failed to fetch updated collections");
      }

      const { collections: updatedCollections } =
        await getCollectionsResponse.json();
      setCollections(
        updatedCollections.map((collection: any) => ({
          collection_name: collection.collection_name,
          document_count: collection.num_entities,
          index_count: collection.num_entities,
        }))
      );

      // 4. Trigger document list refresh and update UI
      onDocumentsUpdate();

      // 5. Close the modal and reset state
      onClose();
      setSelectedFiles([]);
    } catch (err) {
      console.error("Error uploading documents:", err);
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const modalDescription =
    "Upload a collection of source files to provide the model with relevant information for more tailored responses (e.g., marketing plans, research notes, meeting transcripts, sales documents).";

  const collectionSelector = (
    <div className="mb-4">
      <label className="mb-2 block text-sm font-medium">Collection</label>
      <select
        value={selectedCollection}
        onChange={(e) => {
          setSelectedCollection(e.target.value);
        }}
        className="w-full rounded-md bg-neutral-800 px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-[var(--nv-green)]"
      >
        {collections.map((collection) => (
          <option
            key={collection.collection_name}
            value={collection.collection_name}
          >
            {collection.collection_name}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Source"
      description={modalDescription}
      isLoading={isLoading}
      error={error}
      selectedFiles={selectedFiles}
      submitButtonText="Add Source"
      isSubmitDisabled={selectedFiles.length === 0}
      onFileSelect={handleFileSelect}
      onRemoveFile={removeFile}
      onReset={handleReset}
      onSubmit={handleSubmit}
      fileInputId="sourceFileInput"
      customContent={collectionSelector}
    />
  );
}

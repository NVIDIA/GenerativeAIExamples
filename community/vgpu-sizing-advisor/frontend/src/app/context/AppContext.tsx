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

import { createContext, useContext, useState, ReactNode } from "react";
import { Document } from "@/types/documents";
import { Collection } from "@/types/collections";
import { ChatMessage } from "@/types/chat";

// Context State Interface
interface AppState {
  collections: Collection[];
  selectedCollection: string | null;
  documents: Document[];
  chatMessages: ChatMessage[];
  loading: boolean;
  error: string | null;
}

// Context Actions Interface
interface AppContextType extends AppState {
  setCollections: (collections: Collection[]) => void;
  setSelectedCollection: (collectionName: string | null) => void;
  setDocuments: (documents: Document[]) => void;
  addChatMessage: (message: ChatMessage) => void;
  clearChatMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(
    null
  );
  const [documents, setDocuments] = useState<Document[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addChatMessage = (message: ChatMessage) => {
    setChatMessages((prev) => [...prev, message]);
  };

  const clearChatMessages = () => {
    setChatMessages([]);
  };

  return (
    <AppContext.Provider
      value={{
        collections,
        selectedCollection,
        documents,
        chatMessages,
        loading,
        error,
        setCollections,
        setSelectedCollection,
        setDocuments,
        addChatMessage,
        clearChatMessages,
        setLoading,
        setError,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}

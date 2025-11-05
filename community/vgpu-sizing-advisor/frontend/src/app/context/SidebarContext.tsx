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
import { Citation } from "@/types/chat";

interface SidebarContextType {
  activePanel: "citations" | "settings" | null;
  activeCitations: Citation[];
  toggleSidebar: (panel: "citations" | "settings") => void;
  closeSidebar: () => void;
  setActiveCitations: (citations: Citation[]) => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [activePanel, setActivePanel] = useState<
    "citations" | "settings" | null
  >(null);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);

  const toggleSidebar = (panel: "citations" | "settings") => {
    setActivePanel(activePanel === panel ? null : panel);
  };

  const closeSidebar = () => {
    setActivePanel(null);
  };

  return (
    <SidebarContext.Provider
      value={{
        activePanel,
        activeCitations,
        toggleSidebar,
        closeSidebar,
        setActiveCitations,
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}

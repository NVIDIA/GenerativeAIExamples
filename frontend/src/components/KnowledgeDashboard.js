// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useMemo, useState } from "react";
import FileIngestion from "../components/FileIngestion";

/**
 * Standalone "Project Knowledge" page (does not modify existing app routing).
 * - Reuses existing FileIngestion UI for "Add Knowledge" action.
 * - Calls existing backend-rag endpoint: GET /api/rag-status for summary + optional listing.
 * - If /api/rag-status doesn't include per-file rows, table will show an empty state.
 */
export default function ProjectKnowledge() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  // Optional pagination for when a list exists
  const [pageSize, setPageSize] = useState(25);
  const [pageIndex, setPageIndex] = useState(0);

  const loadStatus = async () => {
    try {
      setLoading(true);
      setErr(null);
      const r = await fetch("/api/rag-status", { cache: "no-store" });
      if (!r.ok) throw new Error(`rag-status failed (${r.status})`);
      const j = await r.json();
      setStatus(j);
    } catch (e) {
      setErr(e?.message || "Failed to load status");
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  // NOTE: backend schema is not defined in OpenAPI, so this is defensive:
  const allRows = useMemo(() => {
    if (!status) return [];

    // Try common shapes without assuming:
    // - status.files: [{source,size,type,owner,chunks,avg_score,embedding_model,dimensions,status,file_id}]
    // - status.documents: [...]
    // - status.items: [...]
    const candidates = [status.files, status.documents, status.items, status.data];
    for (const c of candidates) {
      if (Array.isArray(c)) return c;
    }
    return [];
  }, [status]);

  const filteredRows = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allRows;

    return allRows.filter((r) => {
      const s =
        String(r?.source ?? r?.name ?? r?.filename ?? "")
          .toLowerCase()
          .includes(q) ||
        String(r?.type ?? r?.mime_type ?? r?.mimeType ?? "")
          .toLowerCase()
          .includes(q);
      return s;
    });
  }, [allRows, query]);

  const total = filteredRows.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const clampedPageIndex = Math.min(pageIndex, totalPages - 1);

  const pageRows = useMemo(() => {
    const start = clampedPageIndex * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, clampedPageIndex, pageSize]);

  const onPrev = () => setPageIndex((p) => Math.max(0, p - 1));
  const onNext = () => setPageIndex((p) => Math.min(totalPages - 1, p + 1));

  return (
    <div className="chat-container">
      {/* Header row (matches screenshot intent using existing layout) */}
      <div className="messages" style={{ marginBottom: "0.75rem" }}>
        <div className="message assistant">
          <div className="markdown-body" style={{ width: "100%" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <h2 style={{ margin: 0, flex: 1 }}>Project Knowledge</h2>

              <button
                type="button"
                onClick={loadStatus}
                disabled={loading}
                title="Sync"
              >
                {loading ? "Syncing..." : "Sync"}
              </button>

              {/* "Add Knowledge" uses existing Ingest UI below; this button scrolls to it */}
              <button
                type="button"
                onClick={() => {
                  const el = document.getElementById("add-knowledge");
                  el?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
                title="Add Knowledge"
              >
                Add Knowledge ▾
              </button>
            </div>

            {/* Search input */}
            <div style={{ marginTop: "0.75rem" }}>
              <input
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setPageIndex(0);
                }}
                placeholder="Search your documents..."
                style={{ width: "100%" }}
              />
            </div>

            {err ? (
              <div style={{ marginTop: "0.75rem" }}>
                <strong>⚠️ {err}</strong>
              </div>
            ) : null}
          </div>
        </div>

        {/* Table */}
        <div className="message assistant">
          <div className="markdown-body" style={{ width: "100%" }}>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <Th>Source</Th>
                    <Th>Size</Th>
                    <Th>Type</Th>
                    <Th>Owner</Th>
                    <Th>Chunks</Th>
                    <Th>Avg score</Th>
                    <Th>Embedding model</Th>
                    <Th>Dimensions</Th>
                    <Th>Status</Th>
                    <Th></Th>
                  </tr>
                </thead>

                <tbody>
                  {pageRows.length === 0 ? (
                    <tr>
                      <Td colSpan={10}>
                        {allRows.length === 0
                          ? "No per-document rows available from /api/rag-status. (Counts may still be available.)"
                          : "No documents match your search."}
                      </Td>
                    </tr>
                  ) : (
                    pageRows.map((r, idx) => {
                      const source = r?.source ?? r?.name ?? r?.filename ?? "-";
                      const size = r?.size ?? r?.bytes ?? "-";
                      const type = r?.type ?? r?.mime_type ?? r?.mimeType ?? "-";
                      const owner = r?.owner ?? "-";
                      const chunks = r?.chunks ?? r?.num_chunks ?? "-";
                      const avg = r?.avg_score ?? r?.avgScore ?? "-";
                      const emb = r?.embedding_model ?? r?.embeddingModel ?? "-";
                      const dim = r?.dimensions ?? r?.dim ?? "-";
                      const st = r?.status ?? "Active";
                      const fileId = r?.file_id ?? r?.fileId ?? r?.id ?? null;

                      return (
                        <tr key={fileId || idx}>
                          <Td>{String(source)}</Td>
                          <Td>{String(size)}</Td>
                          <Td>{String(type)}</Td>
                          <Td>{String(owner)}</Td>
                          <Td>{String(chunks)}</Td>
                          <Td>
                            {/* pill-ish look without new CSS */}
                            <span
                              style={{
                                display: "inline-block",
                                padding: "2px 8px",
                                borderRadius: "999px",
                                border: "1px solid rgba(255,255,255,0.2)",
                              }}
                            >
                              {String(avg)}
                            </span>
                          </Td>
                          <Td>{String(emb)}</Td>
                          <Td>{String(dim)}</Td>
                          <Td>
                            <span style={{ opacity: 0.9 }}>{String(st)}</span>
                          </Td>
                          <Td style={{ textAlign: "right" }}>
                            {/* Open document if file_id available */}
                            {fileId ? (
                              <button
                                type="button"
                                onClick={() =>
                                  window.open(
                                    `/api/document/${encodeURIComponent(fileId)}`,
                                    "_blank"
                                  )
                                }
                                title="Open"
                              >
                                ⋮
                              </button>
                            ) : (
                              <span style={{ opacity: 0.5 }}>⋮</span>
                            )}
                          </Td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Footer pagination (visual-only, no CSS changes) */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                marginTop: "0.75rem",
                justifyContent: "flex-end",
                opacity: 0.9,
              }}
            >
              <span>Page Size:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPageIndex(0);
                }}
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>

              <span>
                {total === 0
                  ? "0"
                  : `${clampedPageIndex * pageSize + 1} to ${Math.min(
                      (clampedPageIndex + 1) * pageSize,
                      total
                    )} of ${total}`}
              </span>

              <button type="button" onClick={onPrev} disabled={clampedPageIndex === 0}>
                ‹
              </button>
              <button
                type="button"
                onClick={onNext}
                disabled={clampedPageIndex >= totalPages - 1}
              >
                ›
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Add Knowledge section (reuses existing ingestion UI) */}
      <div id="add-knowledge">
        <FileIngestion />
      </div>
    </div>
  );
}

function Th({ children }) {
  return (
    <th
      style={{
        textAlign: "left",
        padding: "10px",
        borderBottom: "1px solid rgba(255,255,255,0.12)",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </th>
  );
}

function Td({ children, colSpan }) {
  return (
    <td
      colSpan={colSpan}
      style={{
        padding: "10px",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
        verticalAlign: "top",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </td>
  );
}
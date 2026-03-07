import React from "react";

export default function DoclingStructuredRenderer({
  items = [],
  query = "",
  apiBase = "http://localhost:8001",
  usePictures = true,
}) {
  const escapeRegExp = (s) => String(s || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  const highlightParts = (text) => {
    const value = String(text || "");
    const needle = String(query || "").trim();
    if (!needle) return [value];

    const re = new RegExp(`(${escapeRegExp(needle)})`, "ig");
    const rawParts = value.split(re);
    return rawParts.map((part, idx) =>
      part.toLowerCase() === needle.toLowerCase() ? (
        <mark
          key={idx}
          style={{
            background: "rgba(255, 230, 0, 0.35)",
            color: "inherit",
            padding: "0 2px",
            borderRadius: 2,
          }}
        >
          {part}
        </mark>
      ) : (
        <React.Fragment key={idx}>{part}</React.Fragment>
      )
    );
  };

  const linkifyText = (text) => {
    const value = String(text || "");
    const parts = value.split(/(https?:\/\/[^\s]+)/g);
    return parts.map((part, idx) => {
      if (/^https?:\/\//i.test(part)) {
        return (
          <a key={idx} href={part} target="_blank" rel="noreferrer">
            {part}
          </a>
        );
      }
      return <React.Fragment key={idx}>{highlightParts(part)}</React.Fragment>;
    });
  };

  const getRelevanceText = (score) =>
    typeof score === "number" ? `Relevance: score ${score.toFixed(3)}` : "Relevance: n/a";

  const itemCardStyle = {
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 10,
    padding: "12px 14px",
    marginTop: "0.75rem",
    background: "rgba(255,255,255,0.02)",
  };

  const metaStyle = {
    display: "flex",
    gap: "0.75rem",
    flexWrap: "wrap",
    alignItems: "center",
    opacity: 0.8,
    fontSize: "0.92rem",
    marginBottom: "0.5rem",
  };

  const badgeStyle = {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: 999,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(255,255,255,0.04)",
    fontSize: "0.8rem",
  };

  if (!items.length) {
    return <div style={{ opacity: 0.75 }}>No rendered results yet.</div>;
  }

  return (
    <div>
      {items
        .filter((item) => usePictures || item.kind !== "picture")
        .map((item, idx) => (
          <div key={`${item.source_file}-${item.kind}-${idx}`} style={itemCardStyle}>
            <div style={metaStyle}>
              <span style={badgeStyle}>{item.kind}</span>
              <span>{getRelevanceText(item.score)}</span>
              {item.page_no != null ? <span>page {item.page_no}</span> : null}
              {item.doc_name ? <span>{item.doc_name}</span> : null}
            </div>

            <div style={{ fontWeight: 700, marginBottom: "0.4rem" }}>
              {highlightParts(item.title || "Untitled")}
            </div>

            {item.image ? (
              <div style={{ marginBottom: "0.65rem" }}>
                <img
                  src={item.image}
                  alt={item.caption || item.title || "Picture"}
                  style={{ maxWidth: "100%", height: "auto", borderRadius: 8 }}
                />
              </div>
            ) : null}

            {item.caption ? (
              <div style={{ whiteSpace: "pre-wrap", marginBottom: "0.5rem" }}>
                {linkifyText(item.caption)}
              </div>
            ) : null}

            {item.body ? <div style={{ whiteSpace: "pre-wrap" }}>{linkifyText(item.body)}</div> : null}

            {item.source_file ? (
              <div style={{ marginTop: "0.75rem" }}>
                <a
                  href={`${apiBase}/api/document/${encodeURIComponent(item.source_file)}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  View Source Document
                </a>
              </div>
            ) : null}
          </div>
        ))}
    </div>
  );
}

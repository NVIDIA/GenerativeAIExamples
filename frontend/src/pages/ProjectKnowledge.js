import React, { useMemo, useRef, useState } from "react";
import FileIngestion from "../components/FileIngestion";

export default function ProjectKnowledge() {
  const API_BASE = "http://192.168.1.142:8001";

  const DISCOVER_QUERIES = useMemo(
    () => [
      ..."abcdefghijklmnopqrstuvwxyz".split(""),
      ..."0123456789".split(""),
      "the",
      "and",
      "of",
      "historic",
      "england",
      "chapel",
      "church",
      "manor",
      "place",
      "gallery",
      "pdf",
    ],
    []
  );

  const [sourceFile, setSourceFile] = useState("");
  const [query, setQuery] = useState("");
  const [renderedResults, setRenderedResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [err, setErr] = useState(null);

  const openPictureCaptionsAnnotations = () => {
    window.open("/picture-captions-annotations", "_blank", "noopener,noreferrer");
  };


  const pageIndexCacheRef = useRef(new Map());
  const docCacheRef = useRef(new Map());
  const docNameCacheRef = useRef(new Map());

  const norm = (s) => String(s || "").replace(/\s+/g, " ").trim();
  const normLower = (s) => norm(s).toLowerCase();
  const escapeHtml = (s) =>
    String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  const escapeRegExp = (s) => String(s || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const highlightHtml = (text, needle) => {
    const safeText = escapeHtml(text);
    const q = String(needle || "").trim();
    if (!q) return safeText;
    const re = new RegExp(`(${escapeRegExp(q)})`, "ig");
    return safeText.replace(re, '<mark class="pk-highlight">$1</mark>');
  };

  const linkifyHtml = (html) =>
    String(html || "").replace(
      /(https?:\/\/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+)/g,
      '<a href="$1" target="_blank" rel="noreferrer">$1</a>'
    );

  const CSS = `
    .pk-results-wrap {
      margin-top: 1rem;
    }
    .pk-results-panel {
      background: #d9d9dd;
      border-radius: 8px;
      padding: 10px;
      color: #202124;
    }
    .pk-results-title {
      margin: 0 0 0.5rem 0;
      color: inherit;
      font-size: 1.1rem;
      font-weight: 600;
    }
    .pk-empty {
      color: #4a4a4a;
      padding: 8px 4px;
    }
    .pk-highlight {
      background: rgba(255, 230, 0, 0.35);
      color: inherit;
      padding: 0 2px;
      border-radius: 2px;
    }
    .pk-reference-card {
      background: #efefef;
      border: 1px solid #d6d6d6;
      border-radius: 6px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
      padding: 12px;
      margin-top: 12px;
      color: #222;
    }
    .pk-reference-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }
    .pk-reference-meta {
      min-width: 0;
      flex: 1;
    }
    .pk-reference-score {
      font-size: 0.95rem;
      color: #6a6a6a;
      margin-bottom: 4px;
    }
    .pk-reference-title {
      font-size: 1rem;
      font-weight: 500;
      line-height: 1.45;
      color: #2b2b2b;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .pk-view-source-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      white-space: nowrap;
      padding: 6px 12px;
      border-radius: 4px;
      border: 1px solid #6d3ea2;
      color: #6d3ea2;
      background: #f8f6fb;
      text-decoration: none;
      font-size: 0.9rem;
      line-height: 1.2;
    }
    .pk-view-source-btn:hover {
      background: #f1ecf8;
    }
    .pk-reference-body {
      white-space: pre-wrap;
      line-height: 1.7;
      color: #303030;
      overflow-wrap: anywhere;
    }
    .pk-reference-footer {
      margin-top: 10px;
      font-size: 0.88rem;
      color: #666;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .pk-reference-image-wrap {
      margin: 0 0 12px 0;
    }
    .pk-reference-image {
      max-width: 100%;
      height: auto;
      display: block;
      border-radius: 8px;
      border: 1px solid #d6d6d6;
      background: #fff;
    }
  `;

  const safeJson = async (resp) => {
    const ct = resp.headers.get("content-type") || "";
    const txt = await resp.text();
    if (ct.includes("application/json")) return JSON.parse(txt);
    throw new Error(`Non-JSON (${resp.status}). First 120: ${txt.slice(0, 120)}`);
  };

  const fetchJson = async (url, options = {}, errorPrefix = "Request failed") => {
    const resp = await fetch(url, options);
    if (!resp.ok) {
      const t = await resp.text();
      throw new Error(`${errorPrefix} ${resp.status}. First 120: ${t.slice(0, 120)}`);
    }
    return safeJson(resp);
  };

  const clearResults = () => setRenderedResults([]);

  const searchApi = async (q, k = 50) =>
    fetchJson(
      `${API_BASE}/api/search`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ query: q, k, use_rag: true }),
      },
      "/api/search failed"
    );

  const uniqueSourceFilesFromSearchData = (searchData) =>
    Array.from(
      new Set((searchData?.results || []).map((r) => String(r?.source_file || "").trim()).filter(Boolean))
    );

  const getCandidateFilesForQuery = async (q) => {
    const data = await searchApi(q, 50);
    return uniqueSourceFilesFromSearchData(data);
  };

  const getPageNo = (obj) => {
    const prov = Array.isArray(obj?.prov) ? obj.prov : [];
    const pageNo = prov[0]?.page_no;
    return Number.isInteger(pageNo) ? pageNo : null;
  };


  const getItemBbox = (obj) => {
    const prov = Array.isArray(obj?.prov) ? obj.prov : [];
    const bbox = prov[0]?.bbox;
    return bbox && typeof bbox === "object" ? bbox : null;
  };

  const getTextByRefMap = (doc) => {
    const map = new Map();
    const texts = Array.isArray(doc?.texts) ? doc.texts : [];
    for (const t of texts) {
      if (t?.self_ref) {
        map.set(t.self_ref, norm(t?.text || t?.orig || ""));
      }
    }
    return map;
  };

  const dedupeTextParts = (parts) => {
    const seen = new Set();
    return (parts || []).filter((t) => {
      const cleaned = norm(t);
      const key = normLower(cleaned);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  const getPictureCaptionTexts = (doc, picture) => {
    const textByRef = getTextByRefMap(doc);
    const captions = Array.isArray(picture?.captions) ? picture.captions : [];
    const refTexts = captions
      .map((c) => {
        if (typeof c === "string") return textByRef.get(c) || c;
        if (c && typeof c === "object") {
          const ref = c.$ref || c.ref;
          if (ref) return textByRef.get(ref) || "";
          return c.text || c.orig || "";
        }
        return "";
      })
      .map((t) => norm(t));

    const directTexts = captions
      .map((c) => {
        if (!c || typeof c !== "object") return "";
        return c.text || c.orig || c.caption || c.label || "";
      })
      .map((t) => norm(t));

    return dedupeTextParts([...refTexts, ...directTexts]);
  };

  const getPictureAnnotationTexts = (picture) => {
    const ann = Array.isArray(picture?.annotations) ? picture.annotations : [];
    const annotationTexts = ann
      .map((a) => {
        if (typeof a === "string") return a;
        if (!a || typeof a !== "object") return "";
        return a?.kind === "description" ? a?.text || "" : "";
      })
      .map((t) => norm(t));

    const meta = picture?.meta && typeof picture.meta === "object" ? picture.meta : {};
    const metaTexts = [meta.description, meta.caption, meta.desc].map((t) => norm(t));

    return dedupeTextParts([...annotationTexts, ...metaTexts]);
  };

  const getPicturePlace = (picture) => {
    const meta = picture?.meta && typeof picture.meta === "object" ? picture.meta : {};
    return norm(meta.place || "");
  };

  const getPictureTextParts = (doc, picture) => {
    const captionTexts = getPictureCaptionTexts(doc, picture);
    const annotationTexts = getPictureAnnotationTexts(picture);
    return dedupeTextParts([...captionTexts, ...annotationTexts]);
  };

  const getPictureCaption = (doc, picture) => {
    const parts = getPictureCaptionTexts(doc, picture);
    return parts.join("\n\n");
  };

  const getPageObject = (doc, pageNo) => {
    const pages = doc?.pages;
    if (!pages || typeof pages !== "object") return null;
    return pages[String(pageNo)] || pages[pageNo] || null;
  };

  const cropPictureFromPage = async (doc, pageNo, bbox, padPx = 2) => {
    try {
      if (!Number.isInteger(pageNo) || !bbox || typeof bbox !== "object") return null;
      const page = getPageObject(doc, pageNo);
      if (!page || typeof page !== "object") return null;
      const imgMeta = page.image;
      let src = null;
      let pxW = 0;
      let pxH = 0;

      if (imgMeta && typeof imgMeta === "object") {
        if (typeof imgMeta.uri === "string" && imgMeta.uri) src = imgMeta.uri;
        if (imgMeta.size && typeof imgMeta.size === "object") {
          pxW = Number(imgMeta.size.width || 0);
          pxH = Number(imgMeta.size.height || 0);
        }
      } else if (typeof imgMeta === "string" && imgMeta) {
        src = imgMeta.startsWith("data:") ? imgMeta : `data:image/png;base64,${imgMeta}`;
      }

      if (!src) return null;

      const img = await new Promise((resolve, reject) => {
        const el = new window.Image();
        el.onload = () => resolve(el);
        el.onerror = reject;
        el.src = src;
      });

      if (!(pxW > 0 && pxH > 0)) {
        pxW = img.naturalWidth || img.width || 0;
        pxH = img.naturalHeight || img.height || 0;
      }
      if (!(pxW > 0 && pxH > 0)) return null;

      const pdfSize = page.size && typeof page.size === "object" ? page.size : {};
      const pdfW = Number(pdfSize.width || 0);
      const pdfH = Number(pdfSize.height || 0);

      let x0 = 0;
      let y0 = 0;
      let x1 = 0;
      let y1 = 0;

      if (pdfW > 0 && pdfH > 0) {
        const l = Number(bbox.l || 0);
        const t = Number(bbox.t || 0);
        const r = Number(bbox.r || 0);
        const b = Number(bbox.b || 0);
        x0 = Math.round((l / pdfW) * pxW);
        x1 = Math.round((r / pdfW) * pxW);
        y0 = Math.round(((pdfH - t) / pdfH) * pxH);
        y1 = Math.round(((pdfH - b) / pdfH) * pxH);
      } else {
        x0 = Number(bbox.l || 0);
        y0 = Number(bbox.t || 0);
        x1 = Number(bbox.r || 0);
        y1 = Number(bbox.b || 0);
      }

      const xs = [x0, x1].sort((a, b) => a - b);
      const ys = [y0, y1].sort((a, b) => a - b);
      x0 = Math.max(0, Math.round(xs[0] - padPx));
      x1 = Math.min(Math.round(pxW), Math.round(xs[1] + padPx));
      y0 = Math.max(0, Math.round(ys[0] - padPx));
      y1 = Math.min(Math.round(pxH), Math.round(ys[1] + padPx));

      if (x1 - x0 < 2 || y1 - y0 < 2) return null;

      const canvas = document.createElement("canvas");
      canvas.width = x1 - x0;
      canvas.height = y1 - y0;
      const ctx = canvas.getContext("2d");
      if (!ctx) return null;
      ctx.drawImage(img, x0, y0, x1 - x0, y1 - y0, 0, 0, x1 - x0, y1 - y0);
      return canvas.toDataURL("image/png");
    } catch (_) {
      return null;
    }
  };

  const fetchDoc = async (sf) => {
    const key = String(sf || "").trim();
    if (!key) return null;
    if (docCacheRef.current.has(key)) return docCacheRef.current.get(key);

    const resp = await fetch(`${API_BASE}/api/document/${encodeURIComponent(key)}`, {
      headers: { Accept: "application/json" },
    });

    if (!resp.ok) {
      docCacheRef.current.set(key, null);
      return null;
    }

    const doc = await safeJson(resp);
    docCacheRef.current.set(key, doc);
    docNameCacheRef.current.set(key, doc?.name ? String(doc.name) : "");
    return doc;
  };

  const getDocName = async (sf) => {
    const key = String(sf || "").trim();
    if (!key) return "";
    if (docNameCacheRef.current.has(key)) return docNameCacheRef.current.get(key) || "";
    const doc = await fetchDoc(key);
    const name = doc?.name ? String(doc.name) : "";
    docNameCacheRef.current.set(key, name);
    return name;
  };

  const buildPageIndexFromDoc = (doc) => {
    const texts = Array.isArray(doc?.texts) ? doc.texts : [];
    const byPage = new Map();

    for (const t of texts) {
      const pageNo = getPageNo(t);
      if (!Number.isInteger(pageNo)) continue;
      const txt = norm(t?.text || t?.orig || "");
      if (!txt) continue;
      if (!byPage.has(pageNo)) byPage.set(pageNo, []);
      byPage.get(pageNo).push(txt);
    }

    return Array.from(byPage.entries())
      .map(([page_no, parts]) => ({ page_no, text_blob_norm: parts.join(" ") }))
      .sort((a, b) => a.page_no - b.page_no);
  };

  const getPageIndexForSourceFile = async (sf) => {
    const key = String(sf || "").trim();
    if (!key) return [];
    if (pageIndexCacheRef.current.has(key)) return pageIndexCacheRef.current.get(key);
    const doc = await fetchDoc(key);
    if (!doc) {
      pageIndexCacheRef.current.set(key, []);
      return [];
    }
    const idx = buildPageIndexFromDoc(doc);
    pageIndexCacheRef.current.set(key, idx);
    return idx;
  };

  const guessPageNoForChunk = async (sf, chunkText) => {
    const key = String(sf || "").trim();
    const chunk = norm(chunkText);
    if (!key || !chunk) return null;
    const idx = await getPageIndexForSourceFile(key);
    if (!idx.length) return null;
    const prefix = chunk.slice(0, 80);
    for (const p of idx) {
      const blob = p.text_blob_norm || "";
      if (blob && (blob.includes(prefix) || blob.startsWith(prefix))) return p.page_no ?? null;
    }
    return null;
  };

  const tableToRows = (table) => {
    const data = table?.data || {};
    const rowCount = data.num_rows;
    const colCount = data.num_cols;
    const cells = data.table_cells || [];
    if (!(Number.isInteger(rowCount) && Number.isInteger(colCount) && rowCount > 0 && colCount > 0)) {
      return null;
    }
    const grid = Array.from({ length: rowCount }, () => Array.from({ length: colCount }, () => ""));
    for (const cell of cells) {
      const txt = String(cell?.text || "").trim();
      const r0 = Number(cell?.start_row_offset_idx ?? 0);
      const r1 = Number(cell?.end_row_offset_idx ?? r0 + 1);
      const c0 = Number(cell?.start_col_offset_idx ?? 0);
      const c1 = Number(cell?.end_col_offset_idx ?? c0 + 1);
      for (let r = r0; r < r1; r++) {
        for (let c = c0; c < c1; c++) {
          if (r >= 0 && r < rowCount && c >= 0 && c < colCount) grid[r][c] = txt;
        }
      }
    }
    return grid;
  };

  const tableHasNeedle = (rows, needle) => {
    const n = normLower(needle);
    if (!n) return false;
    for (const row of rows) {
      for (const cell of row) {
        if (normLower(cell) === n) return true;
      }
    }
    return false;
  };

  const toPlainTable = (rows) => {
    const clean = (rows || []).filter((r) => Array.isArray(r) && r.some((c) => norm(c)));
    return clean.map((r) => r.map((c) => norm(c)).join(" | ")).join("\n");
  };

  const sourceDocumentUrl = (source_file) => `${API_BASE}/api/document/${encodeURIComponent(source_file)}`;

  const makeRenderedCard = ({ key, title, body, source_file, doc_name, page_no, kind, score, footer = [], imageDataUrl = "" }) => ({
    id: key,
    title: title || doc_name || source_file || "—",
    body: body || "",
    source_file: source_file || "",
    doc_name: doc_name || "",
    page_no: page_no,
    kind: kind || "result",
    score: typeof score === "number" ? score : null,
    footer: footer.filter(Boolean),
    imageDataUrl: imageDataUrl || "",
  });

  const shouldHideRenderedResult = (card) => {
    const haystack = normLower([card?.title, card?.body].filter(Boolean).join(" "));
    if (!haystack) return false;

    const blockedPhrases = [
      "does not contain",
      "does not clearly show",
      "does not show",
      "no visible architectural",
      "no architectural",
      "no built-environment",
      "no built environment",
      "no visible built",
      "no visible structure",
      "no visible structures",
      "no visible building",
      "no visible buildings",
      "no structural elements",
      "no architectural elements",
      "monochrome photograph of an individual",
      "individual and does not contain",
      "return exactly: skip",
    ];

    return blockedPhrases.some((phrase) => haystack.includes(phrase));
  };

  const renderCardsHtml = (cards, highlightNeedle) => {
    const visibleCards = (cards || []).filter((card) => !shouldHideRenderedResult(card));
    if (!visibleCards.length) return `<div class="pk-empty">No rendered results.</div>`;
    return visibleCards
      .map((card) => {
        const title = linkifyHtml(highlightHtml(card.title, highlightNeedle));
        const body = linkifyHtml(highlightHtml(card.body, highlightNeedle));
        const relevance = card.score != null ? `Relevance: ${Math.round(card.score * 100)}%` : "Relevance: —";
        const footer = [
          card.kind ? `Type: ${card.kind}` : null,
          card.doc_name ? `Name: ${card.doc_name}` : null,
          Number.isInteger(card.page_no) ? `Page: ${card.page_no}` : null,
          ...card.footer,
        ]
          .filter(Boolean)
          .map((item) => `<span>${linkifyHtml(highlightHtml(item, highlightNeedle))}</span>`)
          .join("");

        const viewSource = card.source_file
          ? `<a class="pk-view-source-btn" href="${escapeHtml(sourceDocumentUrl(card.source_file))}" target="_blank" rel="noreferrer">View Source Document</a>`
          : "";
        const imageBlock = card.imageDataUrl
          ? `<div class="pk-reference-image-wrap"><img class="pk-reference-image" src="${escapeHtml(card.imageDataUrl)}" alt="${escapeHtml(card.title || "picture")}" /></div>`
          : "";

        return `
          <div class="pk-reference-card">
            <div class="pk-reference-header">
              <div class="pk-reference-meta">
                <div class="pk-reference-score">${escapeHtml(relevance)}</div>
                <div class="pk-reference-title">${title}</div>
              </div>
              ${viewSource}
            </div>
            ${imageBlock}
            <div class="pk-reference-body">${body}</div>
            ${footer ? `<div class="pk-reference-footer">${footer}</div>` : ""}
          </div>
        `;
      })
      .join("");
  };

  const extractMatchingTablesFromDoc = (doc, sf, needle) => {
    const out = [];
    const tables = Array.isArray(doc?.tables) ? doc.tables : [];
    for (const t of tables) {
      const rows = tableToRows(t);
      if (!rows) continue;
      if (!tableHasNeedle(rows, needle)) continue;
      out.push(
        makeRenderedCard({
          key: `${sf}-table-${t?.self_ref || out.length}`,
          title: doc?.name || needle,
          body: toPlainTable(rows),
          source_file: String(sf || "").trim(),
          doc_name: doc?.name || "",
          page_no: getPageNo(t),
          kind: "table",
          footer: [rows.length ? `Rows: ${rows.length}` : null],
        })
      );
    }
    return out;
  };

  const extractMatchingGroupsFromDoc = (doc, sf, needle) => {
    const out = [];
    const groups = Array.isArray(doc?.groups) ? doc.groups : [];
    const texts = Array.isArray(doc?.texts) ? doc.texts : [];
    const byRef = new Map();
    for (const t of texts) {
      if (t?.self_ref) byRef.set(t.self_ref, t);
    }
    const n = normLower(needle);
    for (const g of groups) {
      const children = Array.isArray(g?.children) ? g.children : [];
      const parts = [];
      const pages = [];
      for (const ch of children) {
        const ref = ch && typeof ch === "object" ? ch.$ref : null;
        if (!ref) continue;
        const t = byRef.get(ref);
        if (!t) continue;
        const txt = norm(t?.text || t?.orig || "");
        if (!txt) continue;
        parts.push(txt);
        const p = getPageNo(t);
        if (Number.isInteger(p)) pages.push(p);
      }
      const body = parts.join("\n\n");
      if (!body) continue;
      if (n && !normLower(body).includes(n)) continue;
      const pageNo = pages.length ? Math.min(...pages) : null;
      const range = pages.length > 1 ? `${Math.min(...pages)}-${Math.max(...pages)}` : null;
      out.push(
        makeRenderedCard({
          key: `${sf}-group-${g?.self_ref || out.length}`,
          title: doc?.name || `${g?.name || "group"}`,
          body,
          source_file: String(sf || "").trim(),
          doc_name: doc?.name || "",
          page_no: pageNo,
          kind: "group",
          footer: [g?.name ? `Group: ${g.name}` : null, g?.label ? `Label: ${g.label}` : null, range ? `Range: ${range}` : null],
        })
      );
    }
    return out;
  };

  const extractSectionHeaderBlocksFromDoc = (doc, sf, needleOpt) => {
    const out = [];
    const texts = Array.isArray(doc?.texts) ? doc.texts : [];
    const needle = normLower(needleOpt || "");
    for (let i = 0; i < texts.length; i++) {
      const t = texts[i];
      if (!t || typeof t !== "object" || t.label !== "section_header") continue;
      const items = [];
      const pages = [];
      for (let j = i; j < texts.length; j++) {
        const it = texts[j];
        if (!it || typeof it !== "object") continue;
        if (j > i && it.label === "section_header") break;
        const itemText = norm(it?.text || it?.orig || "");
        if (!itemText) continue;
        const p = getPageNo(it);
        if (Number.isInteger(p)) pages.push(p);
        items.push({ label: it?.label || "", text: itemText });
      }
      const headerText = items[0]?.text || "";
      if (needle && !normLower(headerText).includes(needle)) continue;
      const body = items.slice(1).map((it) => it.text).join("\n\n");
      const range = pages.length > 1 ? `${Math.min(...pages)}-${Math.max(...pages)}` : null;
      out.push(
        makeRenderedCard({
          key: `${sf}-header-${t?.self_ref || out.length}`,
          title: headerText || doc?.name || "section_header",
          body,
          source_file: String(sf || "").trim(),
          doc_name: doc?.name || "",
          page_no: getPageNo(t),
          kind: "section_header",
          footer: [range ? `Range: ${range}` : null],
        })
      );
    }
    return out;
  };


  const containsSameMeaning = (a, b) => {
    const x = normLower(a);
    const y = normLower(b);
    if (!x || !y) return false;
    return x === y || x.includes(y) || y.includes(x);
  };

  const uniquePictureParts = (parts) => {
    const out = [];
    for (const part of parts || []) {
      const cleaned = norm(part);
      if (!cleaned) continue;
      if (out.some((existing) => containsSameMeaning(existing, cleaned))) continue;
      out.push(cleaned);
    }
    return out;
  };

  const extractMatchingPicturesFromDoc = async (doc, sf, needle, score = null) => {
    const out = [];
    const pictures = Array.isArray(doc?.pictures) ? doc.pictures : [];
    const n = normLower(needle);

    for (let i = 0; i < pictures.length; i++) {
      const picture = pictures[i];
      if (!picture || typeof picture !== "object") continue;

      const rawCaptionParts = getPictureCaptionTexts(doc, picture);
      const rawAnnotationParts = getPictureAnnotationTexts(picture);
      const place = getPicturePlace(picture);

      const captionParts = uniquePictureParts(rawCaptionParts);
      const annotationParts = uniquePictureParts(
        rawAnnotationParts.filter(
          (part) => !captionParts.some((cap) => containsSameMeaning(cap, part))
        )
      );

      const title = captionParts[0] || annotationParts[0] || doc?.name || `picture ${i + 1}`;

      const bodyParts = uniquePictureParts(
        [
          place ? `Place: ${place}` : "",
          ...captionParts.slice(1),
          ...annotationParts,
        ].filter((part) => !containsSameMeaning(title, part))
      );

      const searchParts = uniquePictureParts([title, ...bodyParts, place]);
      const searchText = searchParts.join("\n\n");
      const body = bodyParts.join("\n\n") || "(no caption or annotation)";
      const matchText = searchText || "picture";

      if (shouldHideRenderedResult({ title, body })) continue;
      if (n && !normLower(matchText).includes(n)) continue;

      const pageNo = getPageNo(picture);
      const bbox = getItemBbox(picture);
      const imageDataUrl = await cropPictureFromPage(doc, pageNo, bbox);

      out.push(
        makeRenderedCard({
          key: `${sf}-picture-${picture?.self_ref || i}`,
          title,
          body,
          source_file: String(sf || "").trim(),
          doc_name: doc?.name || "",
          page_no: pageNo,
          kind: "picture",
          score,
          imageDataUrl,
          footer: [
            place ? `Place: ${place}` : null,
            picture?.self_ref ? `Ref: ${picture.self_ref}` : null,
          ],
        })
      );
    }

    return out;
  };

  const searchAllFiles = async () => {
    try {
      setErr(null);
      setStatus("");
      setLoading(true);
      clearResults();

      const q = query.trim();
      const sfFilter = sourceFile.trim();
      if (!q) throw new Error("Enter a search query.");

      setStatus("Searching (all files)...");
      const searchData = await searchApi(q, 50);
      const filtered = (searchData.results || []).filter((r) => {
        if (!sfFilter) return true;
        return String(r?.source_file || "").trim() === sfFilter;
      });

      const top = filtered.slice(0, 5);
      const cards = [];
      const pictureSeen = new Set();
      setStatus("Building rendered results...");

      for (const r of top) {
        const sf = String(r?.source_file || "").trim();
        const text = typeof r?.text === "string" ? r.text : "";
        let pageNo = null;
        try {
          pageNo = await guessPageNoForChunk(sf, text);
        } catch (_) {
          pageNo = null;
        }
        let docName = "";
        let doc = null;
        try {
          docName = await getDocName(sf);
          doc = await fetchDoc(sf);
        } catch (_) {
          docName = "";
          doc = null;
        }
        const score = typeof r?.score === "number" ? r.score : null;
        cards.push(
          makeRenderedCard({
            key: `${sf}-chunk-${cards.length}`,
            title: docName || sf || "chunk",
            body: text,
            source_file: sf,
            doc_name: docName,
            page_no: pageNo,
            kind: "chunk",
            score,
          })
        );
        if (doc && !pictureSeen.has(sf)) {
          pictureSeen.add(sf);
          cards.push(...(await extractMatchingPicturesFromDoc(doc, sf, q, score)));
        }
        setRenderedResults([...cards]);
      }

      setStatus(
        top.length
          ? `Done. Rendered ${top.length} results.`
          : sfFilter
          ? "No matches for this source_file."
          : "No matches returned."
      );
    } catch (e) {
      setErr(e?.message || String(e));
      setStatus("");
      clearResults();
    } finally {
      setLoading(false);
    }
  };

  const findTables = async () => {
    try {
      setErr(null);
      setStatus("");
      setLoading(true);
      clearResults();

      const needle = query.trim();
      if (!needle) throw new Error('Enter a query (e.g. "General information").');
      const sfFilter = sourceFile.trim();

      if (sfFilter) {
        setStatus(`Loading document ${sfFilter} and scanning tables...`);
        const doc = await fetchDoc(sfFilter);
        if (!doc) throw new Error(`Failed to load /api/document/${sfFilter}`);
        const cards = extractMatchingTablesFromDoc(doc, sfFilter, needle);
        cards.push(...(await extractMatchingPicturesFromDoc(doc, sfFilter, needle)));
        setRenderedResults(cards);
        setStatus(`Done. Rendered ${cards.length} results.`);
        return;
      }

      setStatus("Discovering candidate files via /api/search...");
      const candidateFiles = await getCandidateFilesForQuery(needle);
      const collected = [];
      setStatus(`Scanning tables in ${candidateFiles.length} candidate files...`);
      for (const sf of candidateFiles) {
        const doc = await fetchDoc(sf);
        if (!doc) continue;
        collected.push(...extractMatchingTablesFromDoc(doc, sf, needle));
        collected.push(...(await extractMatchingPicturesFromDoc(doc, sf, needle)));
        setRenderedResults([...collected]);
      }
      setStatus(`Done. Rendered ${collected.length} results.`);
    } catch (e) {
      setErr(e?.message || String(e));
      setStatus("");
      clearResults();
    } finally {
      setLoading(false);
    }
  };

  const findGroups = async () => {
    try {
      setErr(null);
      setStatus("");
      setLoading(true);
      clearResults();

      const needle = query.trim();
      if (!needle) throw new Error('Enter a query (e.g. "Compton Potter\'s Arts Guild").');
      const sfFilter = sourceFile.trim();
      const collected = [];
      const pushLimited = (arr) => {
        for (const item of arr) {
          if (collected.length >= 10) break;
          collected.push(item);
        }
      };

      if (sfFilter) {
        setStatus(`Loading document ${sfFilter} and scanning groups...`);
        const doc = await fetchDoc(sfFilter);
        if (!doc) throw new Error(`Failed to load /api/document/${sfFilter}`);
        pushLimited(extractMatchingGroupsFromDoc(doc, sfFilter, needle));
        collected.push(...(await extractMatchingPicturesFromDoc(doc, sfFilter, needle)));
        setRenderedResults([...collected]);
        setStatus(`Done. Rendered ${collected.length} results.`);
        return;
      }

      setStatus("Discovering candidate files via /api/search...");
      const candidateFiles = await getCandidateFilesForQuery(needle);
      setStatus(`Scanning groups in ${candidateFiles.length} candidate files...`);
      for (const sf of candidateFiles) {
        if (collected.length >= 10) break;
        const doc = await fetchDoc(sf);
        if (!doc) continue;
        pushLimited(extractMatchingGroupsFromDoc(doc, sf, needle));
        collected.push(...(await extractMatchingPicturesFromDoc(doc, sf, needle)));
        setRenderedResults([...collected]);
      }
      setStatus(`Done. Rendered ${collected.length} results.`);
    } catch (e) {
      setErr(e?.message || String(e));
      setStatus("");
      clearResults();
    } finally {
      setLoading(false);
    }
  };

  const findSectionHeaders = async () => {
    try {
      setErr(null);
      setStatus("");
      setLoading(true);
      clearResults();

      const needleOpt = query.trim();
      const sfFilter = sourceFile.trim();

      if (sfFilter) {
        setStatus(`Loading document ${sfFilter} and scanning section headers...`);
        const doc = await fetchDoc(sfFilter);
        if (!doc) throw new Error(`Failed to load /api/document/${sfFilter}`);
        const cards = extractSectionHeaderBlocksFromDoc(doc, sfFilter, needleOpt);
        cards.push(...(await extractMatchingPicturesFromDoc(doc, sfFilter, needleOpt)));
        setRenderedResults(cards);
        setStatus(`Done. Rendered ${cards.length} results.`);
        return;
      }

      const discoveryQuery = needleOpt || "the";
      setStatus("Discovering candidate files via /api/search...");
      const candidateFiles = await getCandidateFilesForQuery(discoveryQuery);
      const collected = [];
      setStatus(`Scanning section headers in ${candidateFiles.length} candidate files...`);
      for (const sf of candidateFiles) {
        const doc = await fetchDoc(sf);
        if (!doc) continue;
        const cards = extractSectionHeaderBlocksFromDoc(doc, sf, needleOpt);
        const pictureCards = await extractMatchingPicturesFromDoc(doc, sf, needleOpt);
        if (cards.length || pictureCards.length) {
          collected.push(...cards, ...pictureCards);
          setRenderedResults([...collected]);
        }
      }
      setStatus(`Done. Rendered ${collected.length} results.`);
    } catch (e) {
      setErr(e?.message || String(e));
      setStatus("");
      clearResults();
    } finally {
      setLoading(false);
    }
  };

  const discoverFiles = async () => {
    try {
      setErr(null);
      setStatus("");
      setLoading(true);
      clearResults();

      const found = new Set();
      setStatus("Discovering source_files via /api/search...");
      for (const q of DISCOVER_QUERIES) {
        const data = await searchApi(q, 50);
        for (const res of data.results || []) {
          if (res?.source_file) found.add(String(res.source_file).trim());
        }
      }

      const discovered = Array.from(found).sort();
      const cards = [];
      setStatus(`Building rendered file list for ${discovered.length} source_files...`);
      for (const sf of discovered) {
        const docName = await getDocName(sf);
        cards.push(
          makeRenderedCard({
            key: `file-${sf}`,
            title: docName || sf,
            body: sf,
            source_file: sf,
            doc_name: docName,
            kind: "source_file",
          })
        );
        setRenderedResults([...cards]);
      }
      setStatus(`Done. Rendered ${cards.length} discovered files.`);
    } catch (e) {
      setErr(e?.message || String(e));
      setStatus("");
      clearResults();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Project Knowledge</h1>
      </header>

      <main className="chat-container">
        <div className="messages">
          <div className="message assistant">
            <div className="markdown-body">
              <style>{CSS}</style>
              <h2 style={{ marginTop: 0 }}>Project Knowledge</h2>

              <div className="controls" style={{ marginTop: "0.75rem" }}>
                <div className="button-group" style={{ gap: "0.5rem", flexWrap: "wrap" }}>
                  <input
                    type="text"
                    value={sourceFile}
                    onChange={(e) => setSourceFile(e.target.value)}
                    placeholder="optional: source_file filter (e.g. <uuid>.json)"
                    style={{ minWidth: 360 }}
                  />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder='query (e.g. Watts Chapel / "General information" / "Compton Potter&#39;s Arts Guild")'
                    style={{ minWidth: 340 }}
                  />
                  <button onClick={searchAllFiles} disabled={loading}>
                    {loading ? "Working..." : "Search Chunks"}
                  </button>
                  <button onClick={findTables} disabled={loading}>
                    {loading ? "Working..." : "Find Tables"}
                  </button>
                  <button onClick={findGroups} disabled={loading}>
                    {loading ? "Working..." : "Find Groups"}
                  </button>
                  <button onClick={findSectionHeaders} disabled={loading}>
                    {loading ? "Working..." : "Find Section Headers"}
                  </button>
                  <button onClick={discoverFiles} disabled={loading}>
                    {loading ? "Working..." : "Discover Files"}
                  </button>
                  <button onClick={openPictureCaptionsAnnotations} disabled={loading}>
                    {loading ? "Working..." : "Picture Captions Annotations"}
                  </button>
                </div>
              </div>

              {status ? <div style={{ marginTop: "0.5rem", opacity: 0.8 }}>{status}</div> : null}

              {err ? (
                <div className="error-message" style={{ marginTop: "0.75rem" }} role="alert">
                  <span className="error-icon">⚠️</span>
                  {err}
                </div>
              ) : null}

              <div className="pk-results-wrap">
                <h3 className="pk-results-title">Rendered results</h3>
                <div
                  className="pk-results-panel"
                  dangerouslySetInnerHTML={{
                    __html: renderCardsHtml(renderedResults, query),
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        <FileIngestion />
      </main>
    </div>
  );
}

import React, { useState, useEffect, useRef } from "react";
import {apiFetch, apiUrl} from "./api";

const STATUS_OPTIONS = [
  "UnderInvestigation",
  "Maintainer Issue",
  "Compability Issue",
  "Fixed"
];

const SEVERITY_COLORS = {
  "CRITICAL": "#ef233c",
  "HIGH": "#ff9800",
  "MEDIUM": "#fbbf24",
  "LOW": "#5eead4",
  "UNKNOWN": "#a1a1aa"
};

// Updated groupRows to handle both per-folder and per-image data
function groupRows(data) {
  let merged = {};
  if (typeof Object.values(data)[0] === "object" && !Array.isArray(Object.values(data)[0])) {
    for (const folder of Object.values(data)) {
      Object.assign(merged, folder);
    }
  } else {
    merged = data;
  }
  return Object.entries(merged).map(([imageVersion, cveMap]) => {
    const vulncount = Object.values(cveMap)
      .filter(v => ((v.status || v.Status || "").toLowerCase() !== "fixed")).length;
    const cveEntries = Object.entries(cveMap);
    const hasFixedOnly = cveEntries.length > 0 && cveEntries.every(
      ([, v]) => ((v.status || v.Status || "").toLowerCase() === "fixed")
    );
    return {
      imageVersion,
      image: imageVersion.split(":")[0],
      version: imageVersion.split(":")[1] || "",
      cves: cveEntries.map(([cve, entry]) => ({ cve, entry })),
      vulncount,
      status: vulncount > 0 ? "vulnerable" : (hasFixedOnly ? "fixed" : "not-vulnerable")
    };
  });
}

const thStyle = { padding: "11px 12px", borderBottom: "2px solid #384567", textAlign: "left", cursor: "pointer" };
const tdStyle = { padding: "10px 22px", borderBottom: "1px solid #384567" };
const cveth = { padding: "8px 10px", background: "#283245", fontWeight: 600, fontSize: "1.04rem", textAlign: "left" };
const cvetd = { padding: "7px 10px", borderBottom: "1px solid #384567", fontSize: "0.99rem" };

function downloadFile(url, filename) {
  fetch(url)
    .then(response => {
      if (!response.ok) throw new Error("Network response was not ok");
      return response.blob();
    })
    .then(blob => {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    })
    .catch(err => {
      alert("Failed to download export: " + err.message);
    });
}

function ImageTable({ data, refresh, jumpTarget, setJumpTarget }) {
  const [expanded, setExpanded] = useState({});
  const [editNotes, setEditNotes] = useState({});
  const [editStatus, setEditStatus] = useState({});
  const [filterStatus, setFilterStatus] = useState("All");
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const [selectedCVEs, setSelectedCVEs] = useState({});
  const [bulkStatus, setBulkStatus] = useState('');
  const [bulkNotes, setBulkNotes] = useState('');

  const rowsUnfiltered = groupRows(data);

  const filteredRows = filterStatus === "All"
    ? rowsUnfiltered
    : rowsUnfiltered.filter(r => r.status.toLowerCase() === filterStatus.toLowerCase());

  const rows = React.useMemo(() => {
    if (!sortConfig.key) return filteredRows;
    const sorted = [...filteredRows].sort((a, b) => {
      let aVal = a[sortConfig.key], bVal = b[sortConfig.key];
      if (sortConfig.key === "vulncount") {
        aVal = parseInt(aVal); bVal = parseInt(bVal);
      }
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [filteredRows, sortConfig]);

  const toggleSort = (key) => {
    setSortConfig(prev =>
      prev.key === key
        ? { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
        : { key, direction: 'asc' }
    );
  };

  const highlightRef = useRef(null);

  useEffect(() => {
    if (jumpTarget && rows.length > 0) {
      let found = false;
      rows.forEach(r => {
        if (r.imageVersion === jumpTarget.image_version) {
          setExpanded(e => ({ ...e, [r.imageVersion]: true }));
          found = true;
        }
      });
      setTimeout(() => {
        if (highlightRef.current) {
          highlightRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
        }
        if (found && setJumpTarget) setTimeout(() => setJumpTarget(null), 800);
      }, 200);
    }
  }, [jumpTarget, rows, setJumpTarget]);

  const onStatusChange = async (imageVersion, cve, status) => {
    await apiFetch("/api/vuln/update", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_version: imageVersion, cve, status })
    });
    setEditStatus(s => ({ ...s, [imageVersion + "|" + cve]: status }));
    refresh && refresh();
  };

  const onNotesChange = async (imageVersion, cve, notes) => {
    await apiFetch("/api/vuln/update", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_version: imageVersion, cve, status: data[imageVersion][cve]?.status, notes })
    });
    setEditNotes(n => ({ ...n, [imageVersion + "|" + cve]: notes }));
    refresh && refresh();
  };

  const handleCVEChecked = (imageVersion, cve, checked) => {
    setSelectedCVEs(prev =>
      checked
        ? { ...prev, [imageVersion + "|" + cve]: { imageVersion, cve } }
        : Object.fromEntries(Object.entries(prev).filter(([k, _]) => k !== imageVersion + "|" + cve))
    );
  };

  const handleBulkStatusChange = e => setBulkStatus(e.target.value);
  const handleBulkNotesChange = e => setBulkNotes(e.target.value);

  const handleBulkUpdate = async () => {
    const payloads = Object.values(selectedCVEs).map(sel => ({
      image_version: sel.imageVersion,
      cve: sel.cve,
      status: bulkStatus,
      notes: bulkNotes
    }));
    await Promise.all(
      payloads.map(p =>
        apiFetch("/api/vuln/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(p)
        })
      )
    );
    setBulkStatus('');
    setBulkNotes('');
    setSelectedCVEs({});
    refresh && refresh();
  };

  return (
    <>
      <div style={{ marginBottom: 12 }}>
        <button onClick={() => downloadFile(apiUrl("/api/export/new_json"), "new_vulnerabilities.json")} style={{ marginRight: 8 }}>
          Download New Vulnerabilities JSON
        </button>
        <button onClick={() => downloadFile(apiUrl("/api/export/new_csv"), "new_vulnerabilities.csv")}>
          Download New Vulnerabilities CSV
        </button>
      </div>

      <div style={{ marginBottom: 10 }}>
        <button
          onClick={() => setFilterStatus("All")}
          style={{ fontWeight: filterStatus === "All" ? "bold" : "normal", marginRight: 8 }}
        >
          All
        </button>
        <button
          onClick={() => setFilterStatus("vulnerable")}
          style={{ fontWeight: filterStatus === "vulnerable" ? "bold" : "normal", marginRight: 8 }}
        >
          Vulnerable
        </button>
        <button
          onClick={() => setFilterStatus("fixed")}
          style={{ fontWeight: filterStatus === "fixed" ? "bold" : "normal" }}
        >
          Fixed
        </button>
      </div>

      <div style={{
        background: "#223", marginBottom: 14, padding: 9, borderRadius: 8, display: "flex", alignItems: "center"
      }}>
        <span style={{ marginRight: 13, fontWeight: 600, color: "#eee" }}>
          Bulk Edit
        </span>
        <select value={bulkStatus} onChange={handleBulkStatusChange} style={{ marginRight: 8 }}>
          <option value="">Set status…</option>
          {STATUS_OPTIONS.map(opt =>
            <option key={opt} value={opt}>{opt}</option>
          )}
        </select>
        <input
          type="text"
          placeholder="Bulk notes…"
          value={bulkNotes}
          onChange={handleBulkNotesChange}
          style={{
            marginRight: 8, padding: "4px 10px", border: "1px solid #384567", borderRadius: 3, minWidth: 100
          }}
        />
        <button
          disabled={Object.keys(selectedCVEs).length === 0 || (!bulkStatus && !bulkNotes)}
          onClick={handleBulkUpdate}
        >
          Apply to Selected ({Object.keys(selectedCVEs).length})
        </button>
      </div>

      <table style={{
        width: "100%", background: "#242b3b", color: "#f5f5fa", borderRadius: 12,
        fontSize: "1.07rem", borderCollapse: "collapse"
      }}>
        <thead style={{ background: "#283245", fontWeight: 700 }}>
          <tr>
            <th style={thStyle}></th>
            <th style={thStyle} onClick={() => toggleSort('image')}>
              Image Name {sortConfig.key === 'image' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}
            </th>
            <th style={thStyle} onClick={() => toggleSort('version')}>
              Version {sortConfig.key === 'version' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}
            </th>
            <th style={thStyle} onClick={() => toggleSort('status')}>
              Status {sortConfig.key === 'status' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}
            </th>
            <th style={thStyle} onClick={() => toggleSort('vulncount')}>
              Vulnerabilities {sortConfig.key === 'vulncount' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <React.Fragment key={r.imageVersion}>
              <tr>
                <td style={{ padding: "8px 13px" }}>
                  <button
                    onClick={() => setExpanded(e => ({ ...e, [r.imageVersion]: !e[r.imageVersion] }))}
                    style={{
                      background: "none", border: "none",
                      color: "#58aeef", fontWeight: 600, fontSize: "1.12rem", cursor: "pointer"
                    }}>{expanded[r.imageVersion] ? "▼" : "▶"}</button>
                </td>
                <td style={tdStyle}>{r.image}</td>
                <td style={tdStyle}>{r.version}</td>
                <td style={tdStyle}>
                  {r.vulncount > 0 ? (
                    <span style={{
                      fontWeight: 700, color: "#fb7185"
                    }}>
                      Vulnerable
                    </span>
                  ) : (
                    <span style={{
                      fontWeight: 700, color: "#33c77a"
                    }}>
                      No Active Vulns
                    </span>
                  )}
                </td>
                <td style={tdStyle}>{r.vulncount}</td>
              </tr>
              {expanded[r.imageVersion] && (
                <tr>
                  <td />
                  <td colSpan={4}>
                    <table style={{ width: "100%", background: "#262E40", borderRadius: 8 }}>
                      <thead>
                        <tr>
                          <th style={cveth}></th>
                          <th style={cveth}>CVE</th>
                          <th style={cveth}>Severity</th>
                          <th style={cveth}>Library</th>
                          <th style={cveth}>Installed Version</th>
                          <th style={cveth}>Fixed Version</th>
                          <th style={cveth}>Description</th>
                          <th style={cveth}>Status</th>
                          <th style={cveth}>Notes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {r.cves.map(({ cve, entry }) => {
                          const disabled = (entry.status || entry.Status) === "Fixed";
                          const key = r.imageVersion + "|" + cve;
                          return (
                            <tr
                              key={cve}
                              ref={jumpTarget &&
                                r.imageVersion === jumpTarget.image_version &&
                                cve === jumpTarget.cve ? highlightRef : null}
                              style={{
                                ...(((entry.status || entry.Status) === "Fixed")
                                  ? { color: "#aaa", background: "#232936", textDecoration: "line-through" }
                                  : {}),
                                ...(jumpTarget &&
                                  r.imageVersion === jumpTarget.image_version &&
                                  cve === jumpTarget.cve
                                  ? { color: "#fff", background: "#234ea570", borderRadius: 6, transition: "background 0.2s" }
                                  : {})
                              }}
                            >
                              <td style={cvetd}>
                                <input
                                  type="checkbox"
                                  checked={!!selectedCVEs[key]}
                                  disabled={disabled}
                                  onChange={e => handleCVEChecked(r.imageVersion, cve, e.target.checked)}
                                />
                              </td>
                              <td style={cvetd}>{cve || "-"}</td>
                              <td style={cvetd}>
                                <span style={{
                                  display: "inline-block",
                                  background: SEVERITY_COLORS[(entry.severity ?? entry.SEVERITY ?? entry.Severity ?? "").toUpperCase()] || "#a1a1aa",
                                  color: "#181820",
                                  fontWeight: 700,
                                  borderRadius: 8,
                                  padding: "2px 13px",
                                  fontSize: "0.99rem",
                                  minWidth: 60,
                                  textAlign: "center",
                                  textTransform: "uppercase"
                                }}>
                                  {((entry.severity ?? entry.SEVERITY ?? entry.Severity) || "UNKNOWN").toUpperCase()}
                                </span>
                              </td>
                              <td style={cvetd}>{entry.library ?? entry.Library ?? entry.pkgName ?? "-"}</td>
                              <td style={cvetd}>{entry.installed_version ?? entry.installedVersion ?? entry.version ?? "-"}</td>
                              <td style={cvetd}>{entry.fixed_version ?? entry.fixedVersion ?? "-"}</td>
                              <td style={cvetd}>{entry.description ?? entry.Description ?? "-"}</td>
                              <td style={cvetd}>
                                <select
                                  style={{
                                    background: "#283245", color: "#fff",
                                    border: "none", borderRadius: 4, padding: "3px 8px"
                                  }}
                                  value={editStatus[r.imageVersion + "|" + cve] ?? entry.status ?? entry.Status}
                                  onChange={e => onStatusChange(r.imageVersion, cve, e.target.value)}
                                  disabled={disabled}
                                >
                                  {STATUS_OPTIONS.map(opt =>
                                    <option key={opt} value={opt}>{opt}</option>
                                  )}
                                </select>
                              </td>
                              <td style={cvetd}>
                                <input
                                  type="text"
                                  style={{
                                    background: "#232936", color: "#eee",
                                    border: "1px solid #384567", borderRadius: 3, width: 120, paddingLeft: 8
                                  }}
                                  value={editNotes[r.imageVersion + "|" + cve] !== undefined
                                    ? editNotes[r.imageVersion + "|" + cve]
                                    : (entry.notes ?? entry.Notes ?? "")}
                                  onChange={e =>
                                    setEditNotes(n =>
                                      ({ ...n, [r.imageVersion + "|" + cve]: e.target.value }))
                                  }
                                  onBlur={e => onNotesChange(r.imageVersion, cve, e.target.value)}
                                  placeholder="Add note..."
                                  disabled={disabled}
                                  onKeyDown={e => {
                                    if (e.key === "Enter") {
                                      e.target.blur();
                                    }
                                  }}
                                />
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} style={{ color: "#aaa", textAlign: "center", padding: "60px" }}>No images found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
}

export default ImageTable;

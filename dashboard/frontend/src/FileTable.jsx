import React from "react";
import StatusSelect from "./StatusSelect";

function FileTable({ files, image, onStatusChange, onNotesChange }) {
  // onNotesChange: function(image, file, cve, value)
  return (
    <div style={{ margin: "18px 0" }}>
      {Object.entries(files).map(([file, entry]) => (
        <div key={file} style={{
          background: "#292d41",
          borderRadius: 10,
          marginBottom: 12,
          padding: "13px 20px",
          boxShadow: "0 2px 12px #18213909"
        }}>
          <div style={{ fontWeight: 600, marginBottom: 9 }}>{file}</div>
          {entry === null ? (
            <div style={{ color: "#aaa" }}>No scan results found.</div>
          ) : (typeof entry === "object" && !Array.isArray(entry) && Object.keys(entry).length === 0) ? (
            <div style={{ color: "#9c9" }}>No vulnerabilities found in this file.</div>
          ) : (Array.isArray(entry) && entry.length === 0) ? (
            <div style={{ color: "#6fd" }}>No vulnerabilities found.</div>
          ) : (
            <table style={{ width: "100%", fontSize: "0.98rem", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={thFile}>CVE</th>
                  <th style={thFile}>Severity</th>
                  <th style={thFile}>Library</th>
                  <th style={thFile}>Installed Version</th>
                  <th style={thFile}>Fixed Version</th>
                  <th style={thFile}>Description</th>
                  <th style={thFile}>Status</th>
                  <th style={thFile}>Notes</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(entry).map(([cve, v]) => (
                  <tr key={cve} style={{ borderBottom: "1px solid #39486c" }}>
                    <td style={tdFile}>{cve}</td>
                    <td style={tdFile}>{v.severity || "Unknown"}</td>
                    <td style={tdFile}>{v.library || v.package || "-"}</td>
                    <td style={tdFile}>{v.installed_version || "-"}</td>
                    <td style={tdFile}>{v.fixed_version || "-"}</td>
                    <td style={{ ...tdFile, maxWidth: 230, whiteSpace: "normal", fontSize: "0.96rem" }}>{v.description || "—"}</td>
                    <td style={tdFile}>
                      <StatusSelect status={v.status} image={image} file={file} cve={cve} onStatusChange={onStatusChange}/>
                    </td>
                    <td style={tdFile}>
                      <input
                        type="text"
                        value={v.notes || ""}
                        style={{
                          width: "120px",
                          background: "#222740",
                          border: "1px solid #314b8b",
                          color: "#dfecf4",
                          borderRadius: 5,
                          fontSize: "0.97rem",
                          padding: "3px 7px"
                        }}
                        placeholder="Add note..."
                        onChange={e => onNotesChange(image, file, cve, e.target.value)}
                        onBlur={e => onNotesChange(image, file, cve, e.target.value, true)}
                          onKeyDown={e => {
                            if (e.key === 'Enter') {
                            e.target.blur(); // This triggers onBlur event, committing the change
                            }
                        }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  );
}
const thFile = {
  padding: "8px 7px",
  background: "#202a37",
  color: "#91cae2",
  fontWeight: 600
};
const tdFile = {
  padding: "8px 12px",
  borderBottom: "1px solid #30364d"
};

export default FileTable;

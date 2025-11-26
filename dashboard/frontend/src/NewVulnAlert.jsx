import React, { useEffect, useState } from "react";
import {apiFetch} from "./api";

// Updated for structure: {folder: {image_version: {cve: vulnObj}}}
function compareFlatVulnData(curr, prev) {
  const added = {};
  for (const [folder, currImages] of Object.entries(curr || {})) {
    const prevImages = prev[folder] || {};
    for (const [image_version, currVulns] of Object.entries(currImages || {})) {
      const prevVulns = prevImages[image_version] || {};
      for (const [cve, vulnObj] of Object.entries(currVulns || {})) {
        if (!(cve in prevVulns)) {
          if (!added[folder]) added[folder] = {};
          if (!added[folder][image_version]) added[folder][image_version] = {};
          added[folder][image_version][cve] = vulnObj;
        }
      }
    }
  }
  return added;
}

function NewVulnAlert({ currData, onJump }) {
  const [added, setAdded] = useState({});
  const [reappeared, setReappeared] = useState([]);

  useEffect(() => {
    apiFetch("/api/vulns/previous")
      .then(r => r.json())
      .then(prevData => setAdded(compareFlatVulnData(currData, prevData)));
  }, [currData]);

  useEffect(() => {
    apiFetch("/api/run_scan", { method: "POST" })
      .then(r => r.json())
      .then(data => {
        if (data.reappeared_alerts && data.reappeared_alerts.length > 0) {
          setReappeared(data.reappeared_alerts);
        }
      });
  }, []);

  // Flatten new CVEs for correct count and list
  const newCVEs = Object.entries(added)
    .flatMap(([folder, images]) =>
      Object.entries(images)
        .flatMap(([image_version, vulns]) =>
          Object.entries(vulns).map(([cve, v]) => ({
            folder,
            image_version,
            cve,
            v
          }))
        )
    );

  const totalNewCVEs = newCVEs.length;

  if (totalNewCVEs === 0 && reappeared.length === 0) return null;

  return (
    <div>
      {totalNewCVEs > 0 && (
        <div
          style={{
            background: "#fb7185",
            color: "#fff",
            fontWeight: 700,
            borderRadius: 9,
            padding: "18px 24px",
            marginBottom: 18,
            fontSize: "1.1rem",
            boxShadow: "0 2px 12px #fbb6c333",
          }}
        >
          🔥 {totalNewCVEs} new vulnerabilities since last scan!
          <details style={{ marginTop: 6, fontWeight: 400, fontSize: "1.03rem" }}>
            <summary>Show new CVEs</summary>
            <ul>
              {newCVEs.map(({ folder, image_version, cve, v }) => (
                <li key={folder + "-" + image_version + "-" + cve} style={{ marginBottom: 6 }}>
                  <button
                    style={{
                      color: "#020000ff",
                      background: "#ffffffff",
                      padding: "2px 12px",
                      borderRadius: 7,
                      margin: "0 8px",
                      fontWeight: 700,
                      cursor: "pointer",
                      border: "none",
                      textDecoration: "underline",
                      outline: "none",
                      boxShadow: "none",
                    }}
                    title="Go to this vulnerability in dashboard"
                    onClick={() => onJump && onJump({ folder, image_version, cve })}
                  >
                    {folder} / {image_version} — <b>{cve}</b>
                  </button>
                  <span style={{ color: "#ffe27a" }}>({v.severity})</span>
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
      {reappeared.length > 0 && (
        <div
          style={{
            background: "#facc15",
            color: "#000",
            fontWeight: 700,
            borderRadius: 9,
            padding: "18px 24px",
            marginBottom: 18,
            fontSize: "1.1rem",
            boxShadow: "0 2px 12px #d2b80755",
          }}
        >
          ⚠️ {reappeared.length} CVEs reappeared after being marked Fixed.
          <details style={{ marginTop: 6, fontWeight: 400, fontSize: "1.03rem" }}>
            <summary>Show Reappeared CVEs</summary>
            <ul>
              {reappeared.map(({ image_version, cve, message, folder }) => (
                <li key={folder + "-" + image_version + "-" + cve} style={{ marginBottom: 6 }}>
                  <button
                    style={{
                      color: "#000",
                      background: "#fffae1",
                      padding: "2px 12px",
                      borderRadius: 7,
                      margin: "0 8px",
                      fontWeight: 700,
                      cursor: "pointer",
                      border: "none",
                      textDecoration: "underline",
                      outline: "none",
                      boxShadow: "none",
                    }}
                    title="Go to this vulnerability in dashboard"
                    onClick={() => onJump && onJump({ folder, image_version, cve })}
                  >
                    {folder} / {image_version} — <b>{cve}</b>
                  </button>
                  <span style={{ color: "#865400" }}>({message})</span>
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}

export default NewVulnAlert;

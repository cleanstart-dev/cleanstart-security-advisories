import React, { useState, useRef, useEffect } from "react";
import { apiFetch, apiUrl } from "./api";
// import React, { useState } from "react";

// function RunScanAndDownload({ onScanStart, onScanDone }) {
//   const [loadingScan, setLoadingScan] = useState(false);
//   const [folderName, setFolderName] = useState("");
//   const [downloading, setDownloading] = useState(false);
//   const [progressLog, setProgressLog] = useState("");
//   const [done, setDone] = useState(false);

//   // Run the scan normally
//   const runScan = async () => {
//     setLoadingScan(true);
//     if (onScanStart) onScanStart();
//     await apiFetch("/api/run_scan", { method: "POST" });
//     setLoadingScan(false);
//     if (onScanDone) onScanDone();
//   };

//   // Download with progress by using GET + EventSource SSE
//   const downloadWithProgress = () => {
//     if (!folderName.trim()) {
//       alert("Please enter a GCP folder name.");
//       return;
//     }
//     if (!window.confirm(`Download results from folder "${folderName.trim()}"? This will clear previous results.`)) {
//       return;
//     }

//     setProgressLog("");
//     setDone(false);
//     setDownloading(true);

//     // Use GET with folder_name query param for SSE connection
//     const url = `http://35.223.170.20:5000/api/progress_download_gcp_results?folder_name=${encodeURIComponent(folderName.trim())}`;
//     const es = new EventSource(url);

//     es.onmessage = (e) => {
//       if (e.data === "DONE") {
//         setProgressLog((prev) => prev + "\nDownload complete!");
//         setDone(true);
//         setDownloading(false);
//         es.close();
//       } else if (e.data.startsWith("ERROR")) {
//         setProgressLog((prev) => prev + "\n" + e.data);
//         setDownloading(false);
//         es.close();
//       } else {
//         setProgressLog((prev) => prev + "\n" + e.data);
//       }
//     };

//     es.onerror = () => {
//       setDownloading(false);
//       es.close();
//     };
//   };

//   return (
//     <div>
//       <button
//         onClick={runScan}
//         disabled={loadingScan}
//         style={{
//           marginBottom: 18,
//           marginRight: 14,
//           padding: "12px 30px",
//           fontWeight: 700,
//           color: "#fff",
//           background: "#255de3",
//           border: "none",
//           borderRadius: 7,
//           fontSize: "1.12rem",
//           cursor: loadingScan ? "not-allowed" : "pointer",
//         }}
//       >
//         {loadingScan ? "Scanning..." : "Run Scan"}
//       </button>

//       <input
//         type="text"
//         value={folderName}
//         onChange={(e) => setFolderName(e.target.value)}
//         placeholder="Enter GCP folder name"
//         style={{
//           padding: "8px 12px",
//           fontSize: "1rem",
//           marginBottom: 18,
//           marginRight: 14,
//         }}
//         disabled={downloading}
//       />
//       <button
//         onClick={downloadWithProgress}
//         disabled={downloading}
//         style={{
//           padding: "12px 30px",
//           fontWeight: 700,
//           color: "#fff",
//           background: "#149e0e",
//           border: "none",
//           borderRadius: 7,
//           fontSize: "1.12rem",
//           cursor: downloading ? "not-allowed" : "pointer",
//         }}
//       >
//         {downloading ? "Downloading..." : "Download"}
//       </button>

//       <pre
//         style={{
//           background: "#1b202b",
//           color: "#80f99e",
//           maxHeight: 270,
//           overflowY: "auto",
//           marginTop: 16,
//           borderRadius: 7,
//           padding: 10,
//           fontSize: "1em",
//           whiteSpace: "pre-wrap",
//         }}
//       >
//         {progressLog.trim()}
//       </pre>

//       {done && (
//         <div style={{ color: "green", fontWeight: 700, marginTop: 10 }}>
//           Download complete!
//         </div>
//       )}
//     </div>
//   );
// }

// export default RunScanAndDownload;


function RunScanAndDownload({ onScanStart, onScanDone }) {
  const [loadingScan, setLoadingScan] = useState(false);
  const [folderName, setFolderName] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [progressLog, setProgressLog] = useState("");
  const [done, setDone] = useState(false);

  // 🔥 Auto-scroll reference
  const logRef = useRef(null);

  // 🔥 Auto-scroll to bottom whenever progressLog updates
  useEffect(() => {
    if (!logRef.current) return;
    logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [progressLog]);

  // Run the scan normally
  const runScan = async () => {
    setLoadingScan(true);
    if (onScanStart) onScanStart();
    await apiFetch("/api/run_scan", { method: "POST" });
    setLoadingScan(false);
    if (onScanDone) onScanDone();
  };

  // Download with progress by using GET + EventSource SSE
  const downloadWithProgress = () => {
    if (!folderName.trim()) {
      alert("Please enter a GCP folder name.");
      return;
    }

    if (!window.confirm(`Download results from folder "${folderName.trim()}"? This will clear previous results.`)) {
      return;
    }

    setProgressLog("");
    setDone(false);
    setDownloading(true);

    // ⭐ FIXED LINE — FULL, CORRECT, NO ERROR
    const url = apiUrl(`/api/progress_download_gcp_results?folder_name=${encodeURIComponent(
      folderName.trim()
    )}`);

    const es = new EventSource(url);

    es.onmessage = (e) => {
      if (e.data === "DONE") {
        setProgressLog((prev) => prev + "\nDownload complete!");
        setDone(true);
        setDownloading(false);
        es.close();
      } else if (e.data.startsWith("ERROR")) {
        setProgressLog((prev) => prev + "\n" + e.data);
        setDownloading(false);
        es.close();
      } else {
        setProgressLog((prev) => prev + "\n" + e.data);
      }
    };

    es.onerror = () => {
      setDownloading(false);
      es.close();
    };
  };

  return (
    <div>
      <button
        onClick={runScan}
        disabled={loadingScan}
        style={{
          marginBottom: 18,
          marginRight: 14,
          padding: "12px 30px",
          fontWeight: 700,
          color: "#fff",
          background: "#255de3",
          border: "none",
          borderRadius: 7,
          fontSize: "1.12rem",
          cursor: loadingScan ? "not-allowed" : "pointer",
        }}
      >
        {loadingScan ? "Scanning..." : "Run Scan"}
      </button>

      <input
        type="text"
        value={folderName}
        onChange={(e) => setFolderName(e.target.value)}
        placeholder="Enter GCP folder name"
        style={{
          padding: "8px 12px",
          fontSize: "1rem",
          marginBottom: 18,
          marginRight: 14,
        }}
        disabled={downloading}
      />
      <button
        onClick={downloadWithProgress}
        disabled={downloading}
        style={{
          padding: "12px 30px",
          fontWeight: 700,
          color: "#fff",
          background: "#149e0e",
          border: "none",
          borderRadius: 7,
          fontSize: "1.12rem",
          cursor: downloading ? "not-allowed" : "pointer",
        }}
      >
        {downloading ? "Downloading..." : "Download"}
      </button>

      <pre
        ref={logRef}
        style={{
          background: "#1b202b",
          color: "#80f99e",
          maxHeight: 270,
          overflowY: "auto",
          marginTop: 16,
          borderRadius: 7,
          padding: 10,
          fontSize: "1em",
          whiteSpace: "pre-wrap",
        }}
      >
        {progressLog.trim()}
      </pre>

      {done && (
        <div style={{ color: "green", fontWeight: 700, marginTop: 1 }}>
          Download complete!
        </div>
      )}
    </div>
  );
}

export default RunScanAndDownload;

 
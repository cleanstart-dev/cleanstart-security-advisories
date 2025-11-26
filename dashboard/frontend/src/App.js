import React, { useState, useEffect } from "react";
import FolderSidebar, { buildPathTree } from "./FolderSidebar";
import TopStats from "./TopStats";
import ImageTable from "./ImageTable";
import RunScanButton from "./RunScanButton";
import NewVulnAlert from "./NewVulnAlert";
import { aggregateDir } from "./helpers";
import LoginPage from './LoginPage';
import { apiFetch } from "./api";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [data, setData] = useState({});
  const [currentDir, setCurrentDir] = useState(""); // '' = all
  const [filter, setFilter] = useState("");
  const [jumpTarget, setJumpTarget] = useState(null);

  useEffect(() => {
    document.body.style.margin = "0";
    document.body.style.padding = "0";
    document.body.style.backgroundColor = "#181e24";
    document.documentElement.style.margin = "0";
    document.documentElement.style.padding = "0";
  }, []);

  useEffect(() => {
    if(isAuthenticated) {
      apiFetch("/api/vulns").then(r => r.json()).then(setData);
    }
  }, [isAuthenticated]);

  function refresh() {
    apiFetch("/api/vulns").then(resp => resp.json()).then(setData);
  }

  function jumpToTarget({ image_version, cve }) {
    setJumpTarget({ image_version, cve });
  }

  // Build tree for sidebar directory navigation
  const pathTree = buildPathTree(data);

  function keyInDir(imageVersion, dir) {
    if (!dir) return true;
    const normDir = dir.replace(/\\/g, "/").replace(/\/+$/, "");
    const normPath = imageVersion.replace(/\\/g, "/");
    return (
      normPath === normDir ||
      normPath.startsWith(normDir + "/")
    );
  }

  // Filter data for current directory/path and search box
  const filtered = Object.fromEntries(
    Object.entries(data)
      .filter(([path]) => keyInDir(path, currentDir))
      .filter(([path]) => !filter || path.toLowerCase().includes(filter.toLowerCase()))
  );

  const { images, cves } = aggregateDir(data, currentDir);

  // Render login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <>
      <FolderSidebar tree={pathTree} onDir={setCurrentDir} currentDir={currentDir} />
      <div
        style={{
          marginLeft: 232,
          minHeight: "100vh",
          background: "#181e24",
          fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
          paddingBottom: 35,
          transition: "margin-left 0.2s"
        }}
      >
        <div style={{ flex: 1, padding: "28px 32px", background: "#22263a" }}>
          <RunScanButton onScanDone={refresh} />
          <NewVulnAlert currData={data} onJump={jumpToTarget} />
          <TopStats data={filtered} dirName={currentDir || "All"} imageCount={Object.keys(filtered).length} />
          <div style={{ margin: "20px 0", display: "flex", justifyContent: "flex-end" }}>
            <input
              value={filter}
              onChange={e => setFilter(e.target.value)}
              placeholder="Search by image or path..."
              style={{
                fontSize: 16,
                borderRadius: 7,
                border: "1.5px solid #314b8b",
                padding: "9px 20px",
                background: "#181a22",
                color: "#eee",
                minWidth: 250,
              }}
            />
          </div>
          <ImageTable
            data={filtered}
            refresh={refresh}
            jumpTarget={jumpTarget}
            setJumpTarget={setJumpTarget}
          />
        </div>
      </div>
      <div style={{
        position: "fixed",
        left: 0,
        right: 0,
        bottom: 0,
        background: "#191b27",
        color: "#50c7f8",
        fontSize: "0.98rem",
        textAlign: "center",
        fontWeight: 500,
        opacity: 0.89,
        padding: "7px 0 6px 0",
        letterSpacing: "0.05em",
        zIndex: 100,
      }}>
        © {new Date().getFullYear()} CleanStart. All rights reserved.
      </div>
    </>
  );
}

export default App;

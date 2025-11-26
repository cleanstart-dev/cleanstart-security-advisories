import React, { useState } from "react";
import {apiFetch} from "./api";
import cleanstartLogo from "./Asset5.svg"; // Use your logo path

function FolderNode({
  label,
  sub,
  fullPath,
  onDir,
  currentDir,
  expanded,
  setExpanded,
}) {
  const isActive = currentDir === fullPath;
  const hasChildren = Object.keys(sub).length > 0;
  const isOpen = !!expanded[fullPath];

  const handleToggle = (e) => {
    e.stopPropagation();
    setExpanded((exp) => ({ ...exp, [fullPath]: !isOpen }));
  };

  return (
    <div>
      <div
        onClick={() => onDir(fullPath)}
        style={{
          display: "flex",
          alignItems: "center",
          background: isActive ? "#385ac4" : "transparent",
          color: isActive ? "#c7e0fb" : "#848e9c",
          borderRadius: 6,
          padding: "7px 2px",
          width: "100%",
          fontWeight: isActive ? 700 : 500,
          fontSize: "1rem",
          cursor: "pointer",
          marginBottom: 2,
          userSelect: "none",
        }}
      >
        {hasChildren && (
          <button
            onClick={handleToggle}
            style={{
              marginRight: 5,
              background: "none",
              border: "none",
              color: "#85a1ed",
              fontWeight: 900,
              fontSize: "1.1rem",
              cursor: "pointer",
              width: 18,
            }}
            tabIndex={-1}
            aria-label="Toggle"
          >
            {isOpen ? "▼" : "▶"}
          </button>
        )}
        {!hasChildren && <span style={{ marginRight: 18 }} />}
        <span>{label}</span>
      </div>
      {hasChildren && isOpen && (
        <div style={{ marginLeft: 14 }}>
          {Object.entries(sub).map(([child, subTree]) => (
            <FolderNode
              key={child}
              label={child}
              sub={subTree}
              fullPath={fullPath ? fullPath + "/" + child : child}
              onDir={onDir}
              currentDir={currentDir}
              expanded={expanded}
              setExpanded={setExpanded}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Convert imageVersion paths to hierarchical tree
function buildPathTree(data) {
  const tree = {};
  Object.keys(data).forEach((imageVersion) => {
    const parts = imageVersion.split(/[\\/]/);
    let node = tree;
    parts.forEach((part) => {
      if (!node[part]) node[part] = {};
      node = node[part];
    });
  });
  return tree;
}

function SyncSqliteButton() {
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");

  const handleSync = async () => {
    if (!window.confirm("Run DB sync? This will push all local data to Postgres.")) return;
    setSyncing(true);
    setSyncMsg("");
    try {
      const resp = await apiFetch("/api/sync_sqlite_to_postgres", { method: "POST" });
      const data = await resp.json();
      if (data.status === "success") setSyncMsg("Sync completed!\n" + data.msg);
      else setSyncMsg("Sync failed!\n" + (data.msg || "Error"));
    } catch (err) {
      setSyncMsg("Sync failed: " + (err.message || "Unknown error"));
    }
    setSyncing(false);
  };

  return (
    <div
      style={{
        margin: "18px 28px",
        background: "#151925",
        borderRadius: 0,
        padding: "0px 0 0px 0",
        textAlign: "center",
      }}
    >
      <button
        onClick={handleSync}
        disabled={syncing}
        style={{
          padding: "12px 10px",
          marginTop: 220,
          fontWeight: 300,
          color: "#fff",
          background: "#963fd8",
          border: "none",
          borderRadius: 7,
          fontSize: "1.08rem",
          cursor: syncing ? "not-allowed" : "pointer",
        }}
      >
        {syncing ? "Syncing..." : "Sync to Postgres"}
      </button>
      {syncMsg && (
        <pre
          style={{
            marginTop: 13,
            background: "#191e2f",
            color: "#ffe2f7",
            padding: 7,
            borderRadius: 7,
            fontSize: "0.99em",
            whiteSpace: "pre-wrap",
          }}
        >
          {syncMsg}
        </pre>
      )}
    </div>
  );
}

const FolderSidebar = ({ tree, onDir, currentDir, user, onLogout }) => {
  const [expanded, setExpanded] = useState({});

  return (
    <div
      style={{
        width: 232,
        background: "#151925",
        position: "fixed",
        top: 0,
        left: 0,
        bottom: 0,
        borderRight: "2.5px solid #23293c",
        paddingTop: 0,
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
        scrollbarWidth: "thin",
        scrollbarColor: "#5586e0 transparent",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "34px 28px 21px 28px",
        }}
      >
        <img
          src={cleanstartLogo}
          alt="CleanStart"
          style={{
            height: 32,
            marginRight: 13,
            borderRadius: 7,
            filter: "drop-shadow(1px 2px 2px #19408C10)",
          }}
        />
      </div>
      <div style={{ padding: "0 30px" }}>
        <h2
          style={{
            color: "#92b7f7",
            fontSize: "1.16rem",
            marginBottom: 20,
            letterSpacing: 1,
            fontWeight: 600,
            userSelect: "none",
          }}
        >
          DIRECTORY
        </h2>
        <div style={{ marginBottom: 5 }}>
          <div
            onClick={() => onDir("")}
            style={{
              background: currentDir === "" ? "#385ac4" : "transparent",
              color: "#c7e0fb",
              borderRadius: 6,
              padding: "7px 2px",
              width: "100%",
              textAlign: "left",
              fontWeight: currentDir === "" ? 700 : 500,
              fontSize: "1rem",
              cursor: "pointer",
              marginBottom: 7,
              userSelect: "none",
            }}
          >
            All
          </div>
          {Object.entries(tree).map(([folder, subTree]) => (
            <FolderNode
              key={folder}
              label={folder}
              sub={subTree}
              fullPath={folder}
              onDir={onDir}
              currentDir={currentDir}
              expanded={expanded}
              setExpanded={setExpanded}
            />
          ))}
        </div>
      </div>

      {/* Add sync button here */}
      <SyncSqliteButton />

      <div style={{ flex: 1 }} />

    </div>
  );
};

export { buildPathTree };
export default FolderSidebar;

import React from "react";

const sidebarItems = [
  { key: "all", label: "All Images", color: "#777777", symbol: "🌐" },
  { key: "vulnerable", label: "Vulnerable", color: "#d94e48", symbol: "🛑" },
  { key: "clean", label: "Vuln-Free", color: "#4ec3d9", symbol: "✅" },
  { key: "notscanned", label: "Not Scanned", color: "#777777", symbol: "❓" }
];

function Sidebar({ view, setView }) {
  return (
    <aside
      style={{
        background: "#121212",
        width: 220,
        borderRight: "2px solid #2a2a2a",
        minHeight: "100vh",
        padding: "40px 20px",
        boxSizing: "border-box",
        color: "#d9d9d9",
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      }}
    >
      <h2
        style={{
          color: "#e2e2e2",
          fontSize: "1.6rem",
          marginBottom: 36,
          fontWeight: "700",
          letterSpacing: "0.05em",
          userSelect: "none",
        }}
      >
        NAVIGATION
      </h2>
      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: 0,
          display: "flex",
          flexDirection: "column",
          gap: 20,
        }}
      >
        {sidebarItems.map(item => (
          <li key={item.key}>
            <button
              onClick={() => setView(item.key)}
              style={{
                width: "100%",
                backgroundColor: view === item.key ? item.color : "transparent",
                color: view === item.key ? "#fff" : "#a6a6a6",
                border: "none",
                borderRadius: 8,
                padding: "16px 12px",
                fontWeight: "700",
                fontSize: "1.1rem",
                display: "flex",
                alignItems: "center",
                gap: 14,
                cursor: "pointer",
                transition: "background-color 0.3s ease",
                userSelect: "none",
              }}
              onMouseEnter={e => {
                if (view !== item.key) e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.1)";
              }}
              onMouseLeave={e => {
                if (view !== item.key) e.currentTarget.style.backgroundColor = "transparent";
              }}
            >
              <span style={{ fontSize: "1.4rem" }}>{item.symbol}</span>
              {item.label}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}

export default Sidebar;

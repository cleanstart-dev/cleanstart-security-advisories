import React, { useState } from "react";
import FileAccordion from "./FileAccordion";

const statusColor = {
  vulnerable: "#e84d2b",
  clean: "#24b94a",
  notscanned: "#bbb"
};

function ImageCard({ img }) {
  const [open, setOpen] = useState(false);
  let tag = "";
  let tagColor = "#bbb";

  // Proper assignments for tag and color
  if (img.status === "vulnerable") {
    tag = "VULNERABLE";
    tagColor = "#e84d2b";
  } else if (img.status === "clean") {
    tag = "VULN-FREE";
    tagColor = "#24b94a";
  } else if (img.status === "notscanned") {
    tag = "NOT SCANNED";
    tagColor = "#bbb";
  }

  return (
    <div style={{
      background: "#fff",
      borderRadius: 16,
      boxShadow: "0 4px 24px #adbbc72a",
      padding: "27px 32px 10px 32px",
      minHeight: 160,
      position: "relative",
      borderLeft: `7px solid ${statusColor[img.status]}`,
      transition: "box-shadow .2s"
    }}>
      <div style={{ marginBottom: 3, fontSize: "1.12rem", fontWeight: 700 }}>{img.image}</div>
      <div style={{
        position: "absolute",
        right: 38, top: 22,
        fontWeight: 800,
        fontSize: "1.1rem",
        color: tagColor,
        letterSpacing: 1,
        opacity: 0.93
      }}>
        {tag}
      </div>
      <div style={{ margin: "18px 0 0 0" }}>
        <button
          onClick={() => setOpen(o => !o)}
          style={{
            padding: "7px 16px",
            background: "#f3f8fe",
            border: "1.5px solid #b5cee7",
            color: "#2d6be3",
            borderRadius: 8,
            fontWeight: 700,
            fontSize: "0.97rem",
            cursor: "pointer",
            marginBottom: 10
          }}
        >
          {open ? "Hide Details" : "Show Details"}
        </button>
        {open &&
          <div style={{ marginTop: 15 }}>
            <FileAccordion files={img.files} />
          </div>
        }
      </div>
    </div>
  );
}

export default ImageCard;

import React, { useState } from "react";
import {apiFetch} from "./api";

const options = [
  "UnderInvestigation",
  "Maintainer Issue",
  "Upstream Fix",
  "Compatibility Issue"
];

function StatusSelect({ status, image, file, cve, onStatusChange }) {
  const [val, setVal] = useState(status);

  function handleChange(e) {
    const newStatus = e.target.value;
    setVal(newStatus);
    apiFetch("/api/vuln/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image_version: image,
        file,
        cve,
        status: newStatus
      })
    }).then(() => onStatusChange && onStatusChange());
  }

  return (
    <select
      value={val}
      onChange={handleChange}
      style={{
        background: "#232e46",
        color: "#fff",
        borderRadius: 7,
        border: "1px solid #5ea0d5",
        padding: "3px 10px"
      }}
    >
      {options.map(o => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}

export default StatusSelect;

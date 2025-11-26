function getStats(data) {
  let merged = {};
  // Merge folders if data is nested by folder
  if (typeof Object.values(data)[0] === "object" && !Array.isArray(Object.values(data)[0])) {
    for (const folder of Object.values(data)) {
      Object.assign(merged, folder);
    }
  } else {
    merged = data;
  }

  let totalImages = Object.keys(merged).length;
  let vulnerableImages = 0;
  let cves = 0;
  let acknowledged = 0;
  let unacknowledged = 0;

  Object.entries(merged).forEach(([image, cveMap]) => {
    const cveList = Object.entries(cveMap || {});
    if (cveList.some(([cve, v]) => (v.status || v.Status) !== "No Vulnerabilities" && (v.status || v.Status || "").toLowerCase() !== "fixed")) {
      vulnerableImages++;
    }
    cves += cveList.filter(([cve, v]) => cve !== "NO_CVE").length;
    for (const [, v] of cveList) {
      if (!v) continue;
      if ((v.status || v.Status) && (v.status || v.Status) !== "UnderInvestigation" && (v.status || v.Status) !== "No Vulnerabilities") {
        acknowledged++;
      } else if ((v.status || v.Status) !== "No Vulnerabilities") {
        unacknowledged++;
      }
    }
  });

  return { totalImages, vulnerableImages, cves, acknowledged, unacknowledged };
}

function TopStats({ data, dirName, imageCount }) {
  const { totalImages, vulnerableImages, cves, acknowledged, unacknowledged } = getStats(data);
  const statStyle = { background: "#232854", color: "#fff", borderRadius: 9, margin: "0 15px 0 0", padding: "14px 28px", display: "inline-block", minWidth: 95, fontWeight: 600 };
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ marginBottom: 9, color: "#5ec7fa", fontWeight: 600, fontSize: "1.15rem" }}>
        {dirName} <span style={{ color: "#bbb", fontSize: ".95em", fontWeight: 500 }}>(Images: {totalImages} | CVEs: {cves})</span>
      </div>
      <span style={statStyle}>Images: {totalImages}</span>
      <span style={{ ...statStyle, background: "#a71a1a" }}>Vulnerable: {vulnerableImages}</span>
      <span style={{ ...statStyle, background: "#5a5b83" }}>Total CVEs: {cves}</span>
      <span style={{ ...statStyle, background: "#11689f" }}>Acknowledged: {acknowledged}</span>
      <span style={{ ...statStyle, background: "#aa4308ff" }}>Unacked: {unacknowledged}</span>
    </div>
  );
}

export default TopStats;

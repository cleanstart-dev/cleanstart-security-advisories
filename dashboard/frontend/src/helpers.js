// Helper: Parse metadata from folder, filename
// Parse image name and version, allowing for suffixes: "argo-cli-fips-3.4.18-dev-27-10-2025.json"
export function parseImageMeta(folder, filename) {
  // Remove .json
  const naked = filename.replace(/\.json$/i, "");
  // Remove date at end (-d-d-d or -dd-mm-yyyy)
  const dateMatch = /-(\d{1,2}-\d{1,2}-\d{4})$/.exec(naked);
  let main = naked;
  if (dateMatch) main = naked.slice(0, -dateMatch[0].length);

  // Match any version with 2-4 numeric segments: 1.2, 1.2.3, 1.2.3.4
  // Optionally with channel (-dev, -prod, etc) as part of version
  const verMatch = /-(\d+\.\d+(?:\.\d+){0,2}(?:-[a-zA-Z0-9]+)?)$/.exec(main);
  let image = main, version = "";
  if (verMatch) {
    version = verMatch[1];
    image = main.slice(0, -verMatch[0].length);
  }
  return { image, version, file: filename, folder };
}

// Recursively build path tree from image keys like batch-2/ct2-stage/xyz/imageA
export function buildPathTree(data) {
  const tree = {};
  Object.keys(data).forEach(k => {
    const parts = k.split(/[\\/]/);
    let node = tree;
    parts.forEach(part => {
      if (!node[part]) node[part] = {};
      node = node[part];
    });
  });
  return tree;
}

// Aggregate stats in a directory subtree
export function aggregateDir(data, dir) {
  let images = [], cves = 0;
  Object.entries(data).forEach(([path, files]) => {
    if (path.startsWith(dir)) {
      images.push(path);
      for (const v of Object.values(files)) {
        if (!v || v.status === "No scan result") continue;
        if (typeof v === "object" && Object.keys(v).length > 0) cves += Object.keys(v).length;
      }
    }
  });
  return { images, cves };
}

export function compareVulnData(curr, prev) {
  // Returns {added: { [image]: {file: {cve: vulnObj}}}}
  const added = {};
  for (const [img, currFiles] of Object.entries(curr)) {
    const prevFiles = prev[img] || {};
    for (const [file, currVulns] of Object.entries(currFiles)) {
      const prevVulns = prevFiles[file] || {};
      if (typeof currVulns === "object" && !Array.isArray(currVulns) && Object.keys(currVulns).length > 0) {
        for (const cve of Object.keys(currVulns)) {
          if (!(cve in prevVulns)) {
            if (!added[img]) added[img] = {};
            if (!added[img][file]) added[img][file] = {};
            added[img][file][cve] = currVulns[cve];
          }
        }
      }
    }
  }
  return added;
}



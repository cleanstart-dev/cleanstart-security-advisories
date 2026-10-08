"""
ONE-TIME SCRIPT: add an OSV 1.7.3 `purl` to every affected[].package entry.

For each advisory JSON file under advisories/ that does NOT have a "withdrawn"
field, every affected[].package with ecosystem "CleanStart" gets:

    "package": {
      "ecosystem": "CleanStart",
      "name": "dino",
      "purl": "pkg:apk/cleanstart/dino?arch=x86_64"
    }

PURL parts:
  type       always "apk" (CleanStart packages are Alpine-style apks)
  namespace  always "cleanstart"
  name       affected[].package.name (lowercased + percent-encoded per the
             purl spec for the apk type, e.g. "libstdc++" -> "libstdc%2B%2B")
  version    deliberately omitted -- OSV recommends a version-less purl in
             affected[].package because versions already live in ranges[]
  arch       qualifier taken from the package's APKBUILD in the CleanStart
             aports repo (branch triam-3.20_stage3_develop). It is only added
             when the APKBUILD pins exactly ONE arch (e.g. arch="noarch" or
             arch="x86_64"). For arch="all" or a multi-arch list the package
             is built for several arches, and a single ?arch= qualifier would
             wrongly narrow it to one, so the qualifier is left off.

HOW APKBUILDs ARE FOUND (no clone -- aports is far too big)
-----------------------------------------------------------
aports is read through the Bitbucket REST API, one file at a time:
  1. list the top-level repo dirs (main/, community/, ...) and the package
     dirs inside them  -> map "package dir name" -> "<repo>/<dir>"
  2. for each distinct package name used by an eligible advisory, download
     only <repo>/<name>/APKBUILD, or <repo>/wf-<name>/APKBUILD (CleanStart's
     own packages mostly live in triam/wf-<pkgname>/). A wf- dir is only
     accepted if its APKBUILD actually builds that package name. If a dir has
     no top-level APKBUILD, its contents are listed and any APKBUILD* file or
     <subdir>/APKBUILD is used instead.
  3. names with no dir of their own (subpackages such as "vault-fips") are
     resolved by trying shorter hyphen-prefixes ("vault", "wf-vault") and
     accepting that APKBUILD only if it lists the name in subpackages=
Every API response is cached in scripts/aports_cache.json, so a --dry-run
followed by the real run downloads nothing twice. Delete that file to re-fetch.

Packages with no APKBUILD found are NOT written by default (reported
instead), since the arch can't be verified. Use --include-unmatched to give
them a purl without an arch qualifier anyway.

Entries that already have a "purl" are left untouched.

AUTH (the repo is private) -- set ONE of:
  BITBUCKET_ACCESS_TOKEN                      repository/workspace access token (Bearer)
  BITBUCKET_USERNAME + BITBUCKET_API_TOKEN    Atlassian account email + API token
  BITBUCKET_USERNAME + BITBUCKET_APP_PASSWORD Bitbucket username + app password
The token only needs repository read access.

USAGE
-----
  Preview only (makes NO changes, prints every package -> purl mapping):
      python scripts/add_package_purls.py --dry-run

  Write purls (and bump "modified") into the advisory files:
      python scripts/add_package_purls.py

  Useful flags:
      --include-unmatched   also write arch-less purls for packages with no APKBUILD
      --limit N             only process the first N eligible advisories
      --cache PATH          where to persist the Bitbucket API cache

OUTPUT (written next to this script, i.e. scripts/)
---------------------------------------------------
  purl_updates.json    every package entry that was (or, with --dry-run,
                       would be) given a purl
  purl_unmatched.json  package names with no APKBUILD in aports
  aports_cache.json    cached Bitbucket API responses, reused across runs
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
ADVISORIES_ROOT = os.path.join(REPO_ROOT, "advisories")

APORTS_SRC_API = ("https://api.bitbucket.org/2.0/repositories/"
                  "cleanstart-security/aports/src/triam-3.20_stage3_develop/")
USER_AGENT = "cleanstart-security-advisories/purl-backfill (one-time script)"

PURL_TYPE = "apk"
PURL_NAMESPACE = "cleanstart"

# abuild forces these subpackage kinds to noarch when the subpackage entry
# doesn't give an explicit ":arch" (see subpkg_set in abuild).
NOARCH_SUBPKG_SUFFIXES = ("-doc", "-openrc", "-lang", "sh-completion", "-pyc")


# --------------------------------------------------------------------------
# Bitbucket API (with on-disk cache)
# --------------------------------------------------------------------------

def auth_header():
    token = os.environ.get("BITBUCKET_ACCESS_TOKEN")
    if token:
        return f"Bearer {token}"
    user = os.environ.get("BITBUCKET_USERNAME")
    secret = os.environ.get("BITBUCKET_API_TOKEN") or os.environ.get("BITBUCKET_APP_PASSWORD")
    if user and secret:
        return "Basic " + base64.b64encode(f"{user}:{secret}".encode()).decode()
    return None


def load_cache(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"dirs": {}, "files": {}}


def save_cache(path, cache):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    try:
        os.replace(tmp, path)
    except OSError as e:
        # OneDrive can hold a lock on the destination mid-sync.
        print(f"Warning: could not replace {path} ({e}); cache left at {tmp}")


class Bitbucket:
    def __init__(self, auth, cache):
        self.auth = auth
        self.cache = cache
        self.calls = 0

    def _get(self, url):
        """GET url; returns the body as text, or None on 404."""
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Authorization": self.auth})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    self.calls += 1
                    return resp.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.calls += 1
                    return None
                if e.code in (401, 403):
                    sys.exit(f"Bitbucket returned {e.code} for {url} -- check the BITBUCKET_* credentials.")
                if e.code == 429 or e.code >= 500:
                    wait = int(e.headers.get("Retry-After") or 0) or 2 ** attempt * 5
                    print(f"  Bitbucket {e.code}, retrying in {wait}s ...", flush=True)
                    time.sleep(wait)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 ** attempt)
        sys.exit(f"Giving up on {url} after repeated failures (cache is saved; just re-run).")

    def _list(self, path):
        """[(type, basename)] for every entry directly under path."""
        entries = []
        url = APORTS_SRC_API + (urllib.parse.quote(path) + "/" if path else "") + "?pagelen=100"
        while url:
            body = self._get(url)
            if body is None:
                break
            page = json.loads(body)
            entries += [(v.get("type"), v["path"].rsplit("/", 1)[-1]) for v in page.get("values", [])]
            url = page.get("next")
        return entries

    def list_dirs(self, path=""):
        """Names of the sub-directories of path (cached)."""
        if path not in self.cache["dirs"]:
            self.cache["dirs"][path] = [n for t, n in self._list(path) if t == "commit_directory"]
        return self.cache["dirs"][path]

    def list_entries(self, path):
        """[[type, name]] of everything directly under path (cached)."""
        entries = self.cache.setdefault("entries", {})
        if path not in entries:
            entries[path] = [list(e) for e in self._list(path)]
        return entries[path]

    def get_file(self, path):
        """Raw file text, or None if it doesn't exist (cached)."""
        if path not in self.cache["files"]:
            self.cache["files"][path] = self._get(APORTS_SRC_API + urllib.parse.quote(path))
        return self.cache["files"][path]


# --------------------------------------------------------------------------
# APKBUILD parsing
# --------------------------------------------------------------------------

# Top-level shell assignments: name="...", name='...', or name=bare-word.
# Double-quoted values may span lines (subpackages= usually does).
ASSIGN_RE = re.compile(
    r'^([A-Za-z_][A-Za-z0-9_]*)=("(?:[^"\\]|\\.)*"|\'[^\']*\'|[^\s#;]*)',
    re.MULTILINE,
)
VAR_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def expand(value, variables):
    """Expand simple $var / ${var} references. Anything fancier (${var%.*},
    $(cmd), ...) is left as-is, and callers treat a leftover '$' as
    unresolved."""
    return VAR_REF_RE.sub(lambda m: variables.get(m.group(1) or m.group(2), m.group(0)), value)


def parse_apkbuild(text):
    """Return the APKBUILD's top-level variables, expanded in definition order
    the way the shell would."""
    variables = {}
    for m in ASSIGN_RE.finditer(text):
        name, raw = m.group(1), m.group(2)
        if raw.startswith("'"):
            value = raw[1:-1]
        elif raw.startswith('"'):
            value = expand(raw[1:-1].replace("\\\n", " "), variables)
        else:
            value = expand(raw, variables)
        variables[name] = value
    return variables


def packages_in_apkbuild(text):
    """Map every package this APKBUILD builds (pkgname + subpackages) to its
    arch= string."""
    variables = parse_apkbuild(text)
    arch = " ".join(variables.get("arch", "").split())
    out = {}
    pkgname = variables.get("pkgname", "")
    if pkgname and "$" not in pkgname:
        out[pkgname] = arch
    for entry in variables.get("subpackages", "").split():
        parts = entry.split(":")
        sub_name = parts[0]
        if not sub_name or "$" in sub_name:
            continue
        if len(parts) > 2 and parts[2]:
            out[sub_name] = parts[2]
        elif sub_name.endswith(NOARCH_SUBPKG_SUFFIXES) or "-lang-" in sub_name:
            out[sub_name] = "noarch"
        else:
            out[sub_name] = arch
    return out


def single_arch(arch):
    """The one concrete arch an APKBUILD arch= value pins, or None if it
    covers several ("all", "all !s390x", "x86_64 aarch64", "", ...)."""
    positives = [a for a in arch.split() if not a.startswith("!")]
    if len(positives) == 1 and positives[0] != "all" and "$" not in positives[0]:
        return positives[0]
    return None


# --------------------------------------------------------------------------
# Package -> APKBUILD resolution
# --------------------------------------------------------------------------

def build_dir_index(bb):
    """Map package dir name -> list of "<repo>/<dir>" across all top-level
    repo dirs of aports. Costs ~1 API call per 100 package dirs."""
    index = {}
    for repo in bb.list_dirs():
        if repo.startswith("."):
            continue
        for pkg_dir in bb.list_dirs(repo):
            index.setdefault(pkg_dir, []).append(f"{repo}/{pkg_dir}")
    return index


def parent_candidates(name):
    """Shorter hyphen-prefixes of name, longest first:
    "foo-bar-fips" -> ["foo-bar", "foo"]."""
    parts = name.split("-")
    return ["-".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]


# CleanStart's own packages mostly live in triam/wf-<pkgname>/ rather than
# triam/<pkgname>/ (e.g. "sonarqube" -> triam/wf-sonarqube/APKBUILD).
DIR_PREFIXES = ("", "wf-")


def apkbuilds_in(pkg_path, bb, depth=3, all_versions=False):
    """Yield (path, text) for the APKBUILD(s) of a package dir. Normally that's
    just <dir>/APKBUILD; if that's missing, look at what the dir does hold:
    APKBUILD-named files, or sub-dirs searched the same way up to `depth`
    levels down.

    Versioned packages keep the current version at <dir>/APKBUILD and other
    versions under <repo>/<dir>/<repo>/<version>/APKBUILD, e.g.
    triam/ruby-fluentd/APKBUILD                  (pkgname=ruby-fluentd-1.19)
    triam/ruby-fluentd/triam/1.18.0/APKBUILD     (pkgname=ruby-fluentd-1.18)
    all_versions=True also searches those sub-dirs when <dir>/APKBUILD exists."""
    text = bb.get_file(f"{pkg_path}/APKBUILD")
    if text is not None:
        yield f"{pkg_path}/APKBUILD", text
        if not all_versions:
            return
    if depth == 0:
        return
    for kind, entry in bb.list_entries(pkg_path):
        if kind == "commit_file" and entry.startswith("APKBUILD") and entry != "APKBUILD":
            text = bb.get_file(f"{pkg_path}/{entry}")
            if text is not None:
                yield f"{pkg_path}/{entry}", text
        elif kind == "commit_directory":
            yield from apkbuilds_in(f"{pkg_path}/{entry}", bb, depth - 1, all_versions)


def resolve_package(name, bb, dir_index):
    """Return {"apkbuild", "arch"} for the APKBUILD that builds `name`, or
    None if none could be found."""
    # 1. A package dir named <name> or wf-<name>.
    for prefix in DIR_PREFIXES:
        for pkg_path in dir_index.get(prefix + name, []):
            for path, text in apkbuilds_in(pkg_path, bb):
                built = packages_in_apkbuild(text)
                if name in built:
                    return {"apkbuild": path, "arch": built[name]}
                if not prefix:
                    # Dir name matches exactly but pkgname is something odd --
                    # fall back to the APKBUILD's own arch= line.
                    arch = " ".join(parse_apkbuild(text).get("arch", "").split())
                    return {"apkbuild": path, "arch": arch}

    # 2. A subpackage of a parent whose dir name is a hyphen-prefix of ours.
    for parent in parent_candidates(name):
        for prefix in DIR_PREFIXES:
            for pkg_path in dir_index.get(prefix + parent, []):
                for path, text in apkbuilds_in(pkg_path, bb):
                    built = packages_in_apkbuild(text)
                    if name in built:
                        return {"apkbuild": path, "arch": built[name]}
    return None


def squash(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def pkgname_candidate_dirs(name, dir_index):
    """Package dirs whose name is related to `name` either way round,
    ignoring punctuation, a "wf-" dir prefix and a "-fips" name suffix:
      dir contains the name   "vault"          -> triam/wf-vault-k8s
      name contains the dir   "spark-sc213-.." -> triam/wf-spark
    The reverse direction only uses dir names of 5+ chars, so short dirs like
    "go" don't pull in every package that happens to contain them."""
    stem = squash(re.sub(r"-fips$", "", name))
    full = squash(name)
    out = []
    for dir_name, paths in dir_index.items():
        base = squash(dir_name[3:] if dir_name.startswith("wf-") else dir_name)
        if stem in squash(dir_name) or (len(base) >= 5 and base in full):
            out += paths
    return sorted(out)


# Package -> APKBUILD path (relative to the aports repo root), checked
# by hand, for packages whose dir name is too different from the package
# name for pkgname_candidate_dirs to find (or that live in a version
# sub-dir). Used as-is, before any searching.
KNOWN_APKBUILDS = {
    "ruby-fluentd-1.18": "triam/ruby-fluentd/triam/1.18.0/APKBUILD",
    "opensearch-dashboards-fips": "triam/wf-opensearch-dashboard-fips/triam/2.19.5/APKBUILD",
    "openjdk8-jdk-azul": "triam/openjdk8-azul/triam/openjdk8-azul/8.0.472/APKBUILD",
    "external-secrets-operator": "triam/wf-external-secrets/triam/2.4.1/APKBUILD",
    "certificate-transparency-trillian-ctserver-fips": "triam/wf-ctlog-trillian-ctserver-fips/triam/1.3.2/APKBUILD",
    "buildkitd": "community/buildkit/community/0.26.3/APKBUILD",
}


def resolve_known(name, bb):
    """Look `name` up in KNOWN_APKBUILDS. The arch comes from the package's
    own entry in that APKBUILD if it builds `name`, else from its arch= line
    (a warning is printed, since the hand-checked path is trusted anyway)."""
    path = KNOWN_APKBUILDS.get(name)
    if not path:
        return None
    text = bb.get_file(path)
    if text is None:
        print(f"  WARNING: KNOWN_APKBUILDS[{name!r}] = {path} does not exist on the branch", flush=True)
        return None
    built = packages_in_apkbuild(text)
    if name in built:
        return {"apkbuild": path, "arch": built[name]}
    print(f"  WARNING: {path} does not build {name!r} (builds {sorted(built)}); "
          f"using its arch= line anyway", flush=True)
    return {"apkbuild": path, "arch": " ".join(parse_apkbuild(text).get("arch", "").split())}


def resolve_by_pkgname(name, bb, dir_index):
    """Broader search for names the directory-name lookup missed: fetch every
    candidate dir's APKBUILDs (including versioned sub-dirs) and accept the
    one whose pkgname= (or one of whose subpackages=) is exactly `name`. If
    several APKBUILDs build it and they disagree on a single arch, the arch
    is dropped."""
    found = resolve_known(name, bb) or resolve_package(name, bb, dir_index)
    if found:
        return found
    matches = []
    for pkg_path in pkgname_candidate_dirs(name, dir_index):
        for path, text in apkbuilds_in(pkg_path, bb, all_versions=True):
            built = packages_in_apkbuild(text)
            if name in built:
                matches.append({"apkbuild": path, "arch": built[name]})
    if not matches:
        return None
    if len({single_arch(m["arch"]) for m in matches}) == 1:
        return {"apkbuild": ", ".join(m["apkbuild"] for m in matches), "arch": matches[0]["arch"]}
    return {"apkbuild": ", ".join(m["apkbuild"] for m in matches),
            "arch": "; ".join(m["arch"] for m in matches)}


# --------------------------------------------------------------------------
# PURL / advisory handling
# --------------------------------------------------------------------------

def make_purl(name, arch):
    purl = f"pkg:{PURL_TYPE}/{PURL_NAMESPACE}/{urllib.parse.quote(name.lower(), safe='-._~')}"
    if arch:
        purl += f"?arch={urllib.parse.quote(arch, safe='-._~')}"
    return purl


def with_purl(package, purl):
    """Copy of the package dict with purl inserted right after "name"."""
    out = {}
    for key, value in package.items():
        out[key] = value
        if key == "name":
            out["purl"] = purl
    if "purl" not in out:
        out["purl"] = purl
    return out


def iter_advisory_files(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            if fn.endswith(".json"):
                yield os.path.join(dirpath, fn)


def now_matching_precision(existing_modified):
    """Match the timestamp precision already used in this file: microseconds
    if the existing 'modified' value has a decimal point, seconds otherwise."""
    now = datetime.now(timezone.utc)
    if existing_modified and "." in existing_modified:
        return now.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    return now.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def needs_purl(package):
    return (bool(package.get("name"))
            and (package.get("ecosystem") or "").lower() == "cleanstart"
            and "purl" not in package)


def load_eligible_advisories(limit):
    """[(path, original_text, data)] for every non-withdrawn advisory."""
    out = []
    for path in iter_advisory_files(ADVISORIES_ROOT):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        data = json.loads(text)
        if "withdrawn" in data:
            continue
        if limit is not None and len(out) >= limit:
            break
        out.append((path, text, data))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="show the results without changing any files")
    parser.add_argument("--include-unmatched", action="store_true",
                        help="also write arch-less purls for packages with no APKBUILD in aports")
    parser.add_argument("--limit", type=int, default=None, help="only process the first N eligible advisories")
    parser.add_argument("--cache", default=os.path.join(SCRIPT_DIR, "aports_cache.json"),
                        help="path to the Bitbucket API response cache file")
    parser.add_argument("--unmatched-only", action="store_true",
                        help="only handle the packages listed in --unmatched-file, matching them by the "
                             "pkgname= of APKBUILDs in related dirs (see pkgname_candidate_dirs)")
    parser.add_argument("--unmatched-file", default=os.path.join(SCRIPT_DIR, "purl_unmatched.json"),
                        help="report from an earlier run to take package names from (default: purl_unmatched.json)")
    args = parser.parse_args()

    auth = auth_header()
    if not auth:
        sys.exit("Set BITBUCKET_ACCESS_TOKEN, or BITBUCKET_USERNAME + BITBUCKET_API_TOKEN "
                 "(or BITBUCKET_APP_PASSWORD) -- see the docstring at the top of this script.")

    print(f"Mode: {'DRY RUN (no files will be changed)' if args.dry_run else 'APPLY (files will be written)'}", flush=True)

    advisories = load_eligible_advisories(args.limit)
    wanted = sorted({p["package"]["name"] for _path, _text, data in advisories
                     for p in data.get("affected", []) or []
                     if needs_purl(p.get("package") or {})})
    resolver = resolve_package
    if args.unmatched_only:
        with open(args.unmatched_file, "r", encoding="utf-8") as f:
            listed = {entry["package"] for entry in json.load(f)}
        wanted = [name for name in wanted if name in listed]
        resolver = resolve_by_pkgname
        print(f"Unmatched-only: {len(listed)} packages in {args.unmatched_file}, "
              f"{len(wanted)} still needing a purl", flush=True)
    print(f"Eligible advisories (not withdrawn): {len(advisories)}; distinct packages needing a purl: {len(wanted)}",
          flush=True)

    cache = load_cache(args.cache)
    bb = Bitbucket(auth, cache)
    resolved = {}
    try:
        print("Listing aports package directories ...", flush=True)
        dir_index = build_dir_index(bb)
        print(f"Found {len(dir_index)} package directories ({bb.calls} API calls)", flush=True)

        for i, name in enumerate(wanted, 1):
            resolved[name] = resolver(name, bb, dir_index)
            if i % 50 == 0:
                print(f"... resolved {i}/{len(wanted)} packages ({bb.calls} API calls so far)", flush=True)
                save_cache(args.cache, cache)
    finally:
        save_cache(args.cache, cache)

    updates = []
    unmatched = {}          # package name -> list of advisory ids
    files_changed = 0

    for path, original_text, data in advisories:
        rel_path = os.path.relpath(path, REPO_ROOT).replace("\\", "/")
        changed = False
        for affected in data.get("affected", []) or []:
            package = affected.get("package") or {}
            if not needs_purl(package) or package["name"] not in resolved:
                continue
            name = package["name"]
            match = resolved.get(name)
            if match is None:
                unmatched.setdefault(name, []).append(data.get("id"))
                if not args.include_unmatched:
                    continue
            purl = make_purl(name, single_arch(match["arch"]) if match else None)
            updates.append({
                "id": data.get("id"), "path": rel_path, "package": name, "purl": purl,
                "apkbuild": match and match["apkbuild"], "apkbuild_arch": match and match["arch"],
            })
            affected["package"] = with_purl(package, purl)
            changed = True

        if changed:
            files_changed += 1
            if not args.dry_run:
                data["modified"] = now_matching_precision(data.get("modified"))
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(data, f, indent=2)
                    if original_text.endswith("\n"):
                        f.write("\n")

    def write_report(name, records):
        out_path = os.path.join(SCRIPT_DIR, name)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        return out_path

    # Unmatched-only runs write to separate files so the purl_unmatched.json
    # they read from isn't overwritten (a --dry-run would otherwise shrink the
    # list the real run then reads).
    if args.unmatched_only:
        updates_name, unmatched_name = "purl_unmatched_resolved.json", "purl_still_unmatched.json"
    else:
        updates_name, unmatched_name = "purl_updates.json", "purl_unmatched.json"
    updates_path = write_report(updates_name, updates)
    unmatched_path = write_report(unmatched_name,
                                  [{"package": k, "advisories": v} for k, v in sorted(unmatched.items())])

    mapping = {u["package"]: u for u in updates}
    print()
    print(f"{'Package':45} {'PURL':70} APKBUILD (arch=)")
    print("-" * 150)
    for name in sorted(mapping):
        u = mapping[name]
        source = f"{u['apkbuild']} ({u['apkbuild_arch']})" if u["apkbuild"] else "NOT IN APORTS"
        print(f"{name:45} {u['purl']:70} {source}")
    if unmatched and not args.include_unmatched:
        print()
        print("No APKBUILD found (skipped -- use --include-unmatched to write arch-less purls):")
        for name in sorted(unmatched):
            print(f"  {name}  ({len(unmatched[name])} advisories)")

    print()
    print(f"Mode: {'DRY RUN (no files changed)' if args.dry_run else 'APPLY (files written)'}")
    print(f"Bitbucket API calls this run (cache hits excluded): {bb.calls}")
    print(f"Advisory files {'that would change' if args.dry_run else 'changed'}: {files_changed}")
    print(f"Package entries {'that would get' if args.dry_run else 'given'} a purl: {len(updates)} "
          f"({len(mapping)} distinct packages)  -> {updates_path}")
    print(f"Distinct packages with no APKBUILD: {len(unmatched)}  -> {unmatched_path}")


if __name__ == "__main__":
    main()

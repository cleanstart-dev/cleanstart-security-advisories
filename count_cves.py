import re
from pathlib import Path
base = Path(__file__).resolve().parent
r = re.compile(r"CVE-[0-9]{4}-[0-9]+", re.I)
s = set()
for f in (base / "advisories").rglob("*.json"):
    try:
        s.update(r.findall(f.read_text()))
    except Exception:
        pass
print(len({x.upper() for x in s}))

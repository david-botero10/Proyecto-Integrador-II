import re
from pathlib import Path

src = Path(__file__).resolve().parents[1] / "Modelo" / "functions.py"
dst = Path(__file__).resolve().parents[1] / "worker" / "src" / "runt_xpaths.py"
text = src.read_text(encoding="utf-8")
pairs = re.findall(r"(\w+_xpath)\s*=\s*'([^']+)'", text)
lines = ['"""XPaths del portal RUNT (consulta vehiculo)."""', ""]
for name, path in pairs:
    lines.append(f"{name.upper()} = \"{path}\"")
dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {len(pairs)} xpaths to {dst}")

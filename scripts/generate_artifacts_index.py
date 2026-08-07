"""Generate Artifacts Index - generuje reports/artifacts_index.json w CI.

PROBLEM (zgloszenie uzytkownika): auto-discovery dokumentow/pilotow/bundli w
panelu dzialo przez listowanie katalogow GitHub API z przegladarki kazdego
uzytkownika (~8 zapytan/ladowanie x auto-refresh co 10 min = ~48/h, plus
reczne odswiezenia) - limit 60 zapytan/h bez autoryzacji byl wyczerpywany,
listy dokumentow znikaly (komunikat degradacji dzialal poprawnie, ale to nie
jest to samo co dzialajaca funkcja).

ROZWIAZANIE: ten sam wzorzec co reports/status.json (write_status.py) - ktory
dziala bezawaryjnie od poczatku WLASNIE dlatego, ze jest GENEROWANY RAZ w CI
(listing z systemu plikow, nie z API), nie odkrywany przez kazda przegladarke
z osobna. Panel czyta ten JEDEN plik przez raw.githubusercontent (bez limitu
API), zamiast wielu zapytan API na kazde ladowanie. Auto-discovery jest
ZACHOWANE - przeniesione o warstwe nizej (z przegladarki do CI), nie
zlikwidowane: nowy dokument/pilot w repo pojawia sie w indeksie przy
najblizszym commicie, bez zadnej zmiany w panel.js ANI w tym skrypcie.

ZERO INTERPRETACJI: kazde pole w indeksie to fakt odczytany wprost z pliku
(sciezka, pierwszy naglowek H1, pole daty juz obecne w tresci, cala tresc
metadata.json bundla/pliku pilota) - zero liczenia, zero oceny. Ksztalt
kazdej pozycji ({path,title,date,ok} dla dokumentow, {path,data,ok} dla
pilotow, {name,path,meta,ok} dla bundli) jest CELOWO identyczny z tym, co
dotychczas produkowaly fetchMdReportsIn()/fetchAllPilotResults()/
fetchAllBundles() w panel.js - zeby zamiana zrodla danych (API -> raw pliku)
nie wymagala zmiany logiki renderujacej, tylko zrodla fetchu.

Uzycie (w CI, po pytest + walidatorach, tak jak write_status.py):
    python scripts/generate_artifacts_index.py [reports/artifacts_index.json]
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_PATH = REPO_ROOT / "reports" / "artifacts_index.json"

# Te same katalogi co dotychczasowy fetchAllReports() w panel.js (Raporty +
# PC-001 Dokumenty czytaja z tej samej puli, filtrujac po nazwie pliku).
DOC_MD_DIRS = ["", "docs", "publications", "clos_academy", "reports/pilot"]

# Ten sam wzorzec co MD_DATE_HEADER_RE/FILENAME_DATE_RE w panel.js (odmrozenie
# dat) - nagłowek "**Data:** ..." ma pierwszenstwo, potem data w nazwie pliku.
MD_DATE_HEADER_RE = re.compile(r"\*\*Data:\*\*\s*(\S+)")
FILENAME_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)

# Ta sama lista i kolejnosc co CONTENT_DATE_FIELDS w panel.js.
CONTENT_DATE_FIELDS = ["generated_at", "timestamp", "date", "bundled_at", "preregistration_date"]


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def extract_md_date(text, filename):
    m = MD_DATE_HEADER_RE.search(text)
    if m:
        return m.group(1)
    fm = FILENAME_DATE_RE.search(filename)
    if fm:
        return fm.group(1)
    return None


def extract_json_date(obj):
    if not isinstance(obj, dict):
        return None
    for key in CONTENT_DATE_FIELDS:
        v = obj.get(key)
        if v:
            return v
    return None


def scan_md_documents():
    docs = []
    seen = set()
    for d in DOC_MD_DIRS:
        dir_path = (REPO_ROOT / d) if d else REPO_ROOT
        if not dir_path.is_dir():
            continue
        for f in sorted(dir_path.glob("*.md")):
            rel = _rel(f)
            if rel in seen:
                continue
            seen.add(rel)
            try:
                text = _read_text(f)
                m = H1_RE.search(text)
                docs.append({
                    "path": rel, "title": m.group(1).strip() if m else rel,
                    "date": extract_md_date(text, f.name), "ok": True,
                })
            except Exception as exc:
                docs.append({"path": rel, "title": rel, "date": None, "ok": False, "error": str(exc)})
    return docs


def scan_json_documents():
    """publications/*.json jako dokumenty (obok *.md) - kazdy dokument
    protokolu ma bliznaczy JSON (SPECYFIKACJA_KANONICZNA_PC_001.md §1), dotad
    niewidoczny w indeksie dokumentow panelu."""
    docs = []
    pub_dir = REPO_ROOT / "publications"
    if not pub_dir.is_dir():
        return docs
    for f in sorted(pub_dir.glob("*.json")):
        rel = _rel(f)
        try:
            data = json.loads(_read_text(f))
            title = data.get("title") if isinstance(data, dict) else None
            docs.append({
                "path": rel, "title": title or f.name,
                "date": extract_json_date(data), "ok": True,
            })
        except Exception as exc:
            docs.append({"path": rel, "title": f.name, "date": None, "ok": False, "error": str(exc)})
    return docs


def scan_pilots():
    pilots = []
    pilot_dir = REPO_ROOT / "reports" / "pilot"
    if not pilot_dir.is_dir():
        return pilots
    for f in sorted(pilot_dir.glob("*.json")):
        rel = _rel(f)
        try:
            data = json.loads(_read_text(f))
            pilots.append({"path": rel, "data": data, "ok": True})
        except Exception as exc:
            pilots.append({"path": rel, "data": None, "ok": False, "error": str(exc)})
    return pilots


def scan_bundles():
    bundles = []
    pub_dir = REPO_ROOT / "publications"
    if not pub_dir.is_dir():
        return bundles
    for sub in sorted(p for p in pub_dir.iterdir() if p.is_dir()):
        meta_path = sub / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            data = json.loads(_read_text(meta_path))
            bundles.append({"name": sub.name, "path": _rel(meta_path), "meta": data, "ok": True})
        except Exception as exc:
            bundles.append({"name": sub.name, "path": _rel(meta_path), "meta": None, "ok": False, "error": str(exc)})
    return bundles


def build_index():
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "documents": scan_md_documents() + scan_json_documents(),
        "pilots": scan_pilots(),
        "bundles": scan_bundles(),
    }


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT_PATH
    index = build_index()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(
        f"generate_artifacts_index: zapisano {out_path} "
        f"({len(index['documents'])} dokumentow, {len(index['pilots'])} pilotow, "
        f"{len(index['bundles'])} bundli)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

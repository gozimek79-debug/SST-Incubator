"""Konwerter SPECYFIKACJI KANONICZNEJ PC-001: markdown -> json (mechaniczne odwzorowanie).

Niezalezna implementacja wzgledem prototypu audytora (spec_md_to_json.py, root repo,
material referencyjny, nie do wklejenia). Ten plik czyta wylacznie STRUKTURE markdowna:
naglowki (numerowane i nie), tabele jako dane (nie tekst), cytaty, listy, bloki kodu,
akapity. Nie wyciaga zadnej "wartosci", nie normalizuje, nie uzupelnia brakow -
kazda taka proba uczynilaby JSON drugim zrodlem znaczenia obok markdowna (zasada C-001,
SPECYFIKACJA_KANONICZNA_PC_001_v1.0.md §0.2).

DECYZJA: BRAK HASHA MARKDOWNA W JSON (odstepstwo od prototypu, do zatwierdzenia przez CTO)
---------------------------------------------------------------------------------------
Prototyp osadza `source_document_sha256` w JSON i traktuje to jako swiadomy, udokumentowany
wyjatek od C-001 ("prowenencja artefaktu, nie wartosc eksperymentu" - ale wyjatek to wyjatek).
Aktualny tekst specyfikacji (§8, §9 test nr 7) rowniez opisuje mechanizm wykrywania rozjazdu
jako porownanie osadzonego hasha.

Ta implementacja NIE osadza hasha i nie potrzebuje wyjatku od C-001 wcale. Detekcja rozjazdu
md/json jest w calosci obowiazkiem walidatora (scripts/validate_canonical_spec.py, test 7):
walidator wywoluje `convert()` na BIEZACYM markdownie w pamieci i porownuje wynik STRUKTURALNIE
z zacommitowanym JSON-em. Poniewaz `convert()` jest funkcja czysta (brak czasu, losowosci,
srodowiska - tylko tekst wejsciowy), rownosc strukturalna wykrywa oba przypadki naraz:
  (a) markdown zmieniony bez regeneracji JSON-a,
  (b) JSON edytowany recznie (nawet jesli markdown sie nie zmienil).
Podejscie z hashem osadzonym w JSON wykrywa TYLKO przypadek (a) o ile ktos nie dotknie samego
pola `source_document_sha256` przy recznej edycji - podejscie "regeneruj i porownaj" jest
scisle mocniejsze i nie wymaga zadnego wyjatku od C-001, bo JSON nie niesie zadnej wartosci
pochodzacej z hashowania.

Konsekwencja: opis w §8/§9 specyfikacji ("test §9 nr 7 porownuje skrot markdowna zapisany
w JSON") wymaga korekty na "test §9 nr 7 regeneruje JSON z biezacego markdowna w pamieci
i porownuje strukturalnie z zacommitowanym plikiem" - ta zmiana tresci nalezy do CTO,
nie zostala tu wykonana samodzielnie.

Dodatkowa roznica wzgledem prototypu: prototyp osadza literaly "version": "1.0" i
"experiment_id": "PC-001" w kodzie konwertera, mimo ze nie sa to pola oznaczone
pogrubieniem w naglowku dokumentu (sa jedynie podciagiem tytulu) - to jest drobna
interpretacja tresci. Ta implementacja tego nie robi: tytul jest przenoszony w calosci
(zawiera "PC-001" i "v1.0" jako podciagi), a osobne pola sa tworzone wylacznie z faktycznie
oznaczonych "**Klucz:** wartosc" linii naglowka dokumentu.

Uzycie: python scripts/spec_md_to_json.py <spec.md> [wyjscie.json]
"""

import json
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^(#{2,6})\s+(.*)$")  # H1 jest tytulem dokumentu, obslugiwany osobno
NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*[a-z]?)[.)]?\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
BOLD_LEAD_RE = re.compile(r"^\*\*(.+?):?\*\*")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.*)$")
META_PAIR_RE = re.compile(r"\*\*(.+?):\*\*\s*(.*?)(?=\s*·\s*\*\*|\s*$)")


def _slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _split_table_row(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _try_parse_table(lines, i):
    """Tabela markdown poczawszy od linii i -> (blok, indeks za tabela). (None, i) gdy to nie tabela."""
    if i + 1 >= len(lines):
        return None, i
    if not lines[i].lstrip().startswith("|"):
        return None, i
    if not TABLE_SEP_RE.match(lines[i + 1]):
        return None, i
    header = _split_table_row(lines[i])
    rows = []
    j = i + 2
    while j < len(lines) and lines[j].lstrip().startswith("|"):
        cells = _split_table_row(lines[j])
        cells += [""] * (len(header) - len(cells))
        rows.append({(header[k] or f"col_{k}"): cells[k] for k in range(len(header))})
        j += 1
    return {"type": "table", "columns": header, "rows": rows}, j


def parse_content_blocks(lines):
    """Bloki tresci wewnatrz jednej sekcji, w kolejnosci wystapienia w markdownie."""
    blocks = []
    para_buf = []
    quote_buf = []
    i = 0

    def flush_para():
        if para_buf:
            text = " ".join(para_buf).strip()
            block = {"type": "paragraph", "text": text}
            m = BOLD_LEAD_RE.match(text)
            if m:
                block["lead"] = m.group(1).strip()
            blocks.append(block)
            para_buf.clear()

    def flush_quote():
        if quote_buf:
            blocks.append({"type": "note", "text": " ".join(quote_buf).strip()})
            quote_buf.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "---":
            flush_para()
            flush_quote()
            i += 1
            continue

        if line.startswith("```"):
            flush_para()
            flush_quote()
            lang = line[3:].strip()
            j = i + 1
            code_lines = []
            while j < len(lines) and not lines[j].startswith("```"):
                code_lines.append(lines[j])
                j += 1
            block = {"type": "code", "text": "\n".join(code_lines)}
            if lang:
                block["language"] = lang
            blocks.append(block)
            i = j + 1
            continue

        table, j = _try_parse_table(lines, i)
        if table is not None:
            flush_para()
            flush_quote()
            blocks.append(table)
            i = j
            continue

        if line.lstrip().startswith(">"):
            flush_para()
            quote_buf.append(line.lstrip()[1:].strip())
            i += 1
            continue
        elif quote_buf:
            flush_quote()

        list_m = LIST_ITEM_RE.match(line)
        if list_m:
            flush_para()
            items = []
            while i < len(lines):
                mm = LIST_ITEM_RE.match(lines[i])
                if mm:
                    items.append(mm.group(1).strip())
                    i += 1
                elif lines[i].strip() and items:
                    items[-1] = items[-1] + " " + lines[i].strip()
                    i += 1
                else:
                    break
            blocks.append({"type": "list", "items": items})
            continue

        if stripped == "":
            flush_para()
            i += 1
            continue

        para_buf.append(stripped)
        i += 1

    flush_para()
    flush_quote()
    return blocks


def _parse_preamble(lines, end):
    """Tytul dokumentu (# ...) i pary '**Klucz:** wartosc' przed pierwszym separatorem."""
    title = ""
    meta = {}
    for line in lines[:end]:
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        for key_raw, val_raw in META_PAIR_RE.findall(line):
            key = key_raw.strip().lower().replace(" ", "_")
            val = val_raw.strip()
            meta[key] = (meta[key] + " " + val).strip() if key in meta else val
    return title, meta


def convert(md_text, source_filename):
    """Czysta funkcja: tekst markdowna -> struktura danych. Deterministyczna, bez efektow ubocznych."""
    lines = md_text.splitlines()
    first_sep = next((i for i, l in enumerate(lines) if l.strip() == "---"), len(lines))
    title, meta = _parse_preamble(lines, first_sep)

    sections = []
    current = None
    buf = []

    def close_current():
        if current is not None:
            current["blocks"] = parse_content_blocks(buf)
            sections.append(current)

    for idx, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if not m:
            if current is not None:
                buf.append(line)
            continue
        close_current()
        buf = []
        hashes, title_text = m.groups()
        title_text = title_text.strip()
        num_m = NUMBERED_RE.match(title_text)
        section_id = num_m.group(1) if num_m else _slugify(title_text)
        current = {
            "id": section_id,
            "numbered": bool(num_m),
            "level": len(hashes),
            "title": title_text,
            "start_line": idx + 1,
        }
    close_current()

    return {
        "document_type": "canonical_specification_mirror",
        "generator": "scripts/spec_md_to_json.py",
        "generated_from": source_filename,
        "note": (
            "JSON jest mechanicznym odwzorowaniem markdowna kanonicznego, bez interpretacji "
            "tresci. Przy rozbieznosci rozstrzyga markdown, nastepnie adres, na ktory markdown "
            "wskazuje (SPECYFIKACJA_KANONICZNA_PC_001_v1.0.md §0.3). Ten plik nie jest recznie "
            "edytowalny - regenerowac przez `python scripts/spec_md_to_json.py "
            f"{source_filename}`. Zgodnosc z markdownem sprawdza "
            "scripts/validate_canonical_spec.py (test 7) przez regeneracje w pamieci, nie "
            "przez porownanie hasha."
        ),
        "title": title,
        "meta": meta,
        "sections": sections,
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    src = Path(argv[1])
    out = Path(argv[2]) if len(argv) > 2 else src.with_suffix(".json")
    raw = src.read_text(encoding="utf-8")
    data = convert(raw, src.name)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n_sections = len(data["sections"])
    n_tables = sum(1 for s in data["sections"] for b in s["blocks"] if b["type"] == "table")
    n_rows = sum(
        len(b["rows"]) for s in data["sections"] for b in s["blocks"] if b["type"] == "table"
    )
    print(f"zapisano: {out}")
    print(f"sekcji: {n_sections} - tabel: {n_tables} - wierszy w tabelach: {n_rows}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

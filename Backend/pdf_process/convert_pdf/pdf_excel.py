from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

import pdfplumber
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger("pdf_to_excel")

PathLike = Union[str, Path]

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
_HEADER_FILL = PatternFill("solid", start_color="1F4E78")
_HEADER_FONT = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
_BODY_FONT = Font(name="Calibri", size=10)
_THIN = Side(style="thin", color="BFBFBF")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_ILLEGAL_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_NUMBER = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")


@dataclass
class ConversionResult:
    pdf: Path
    xlsx: Optional[Path] = None
    pages: int = 0
    tables: int = 0
    text_pages: int = 0
    empty_pages: List[int] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            msg = (f"OK   {self.pdf.name} -> {self.xlsx}  "
                   f"(pages={self.pages}, tables={self.tables}, text_pages={self.text_pages})")
            if self.empty_pages:
                msg += f"  [no text on pages {self.empty_pages} - scanned? OCR needed]"
            return msg
        return f"FAIL {self.pdf} : {self.error}"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _clean(value) -> object:
    """Normalise a cell: strip, remove illegal chars, convert numbers."""
    if value is None:
        return None
    s = _ILLEGAL_XML.sub("", str(value)).replace("\n", " ").strip()
    if s == "":
        return None
    if _NUMBER.match(s) and any(ch.isdigit() for ch in s) and not s.endswith("%"):
        neg = s.startswith("(") and s.endswith(")")
        t = s.strip("()").replace(",", "")
        # Keep leading-zero IDs (e.g. 00123) as text so they are not corrupted.
        if len(t.lstrip("-")) > 1 and t.lstrip("-").startswith("0") and "." not in t:
            return s
        try:
            num = float(t) if "." in t else int(t)
        except ValueError:
            return s
        if neg:
            num = -num
        return num
    return s


def _unique_sheet_name(wb: Workbook, base: str) -> str:
    base = re.sub(r"[\[\]\:\*\?\/\\]", "_", base)[:31]
    name, i = base, 1
    while name in wb.sheetnames:
        suffix = f"_{i}"
        name = base[: 31 - len(suffix)] + suffix
        i += 1
    return name


def _write_table(ws, rows: Sequence[Sequence]) -> None:
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=_clean(val))
            cell.border = _BORDER
            if r_idx == 1:
                cell.fill, cell.font = _HEADER_FILL, _HEADER_FONT
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                cell.font = _BODY_FONT
                cell.alignment = Alignment(vertical="top", wrap_text=True)
    _autosize(ws)
    ws.freeze_panes = "A2"
    if rows and rows[0]:
        ws.auto_filter.ref = ws.dimensions


def _autosize(ws, min_w: int = 8, max_w: int = 60) -> None:
    widths: dict = {}
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                widths[c.column] = max(widths.get(c.column, 0), len(str(c.value)))
    for col, w in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = max(min_w, min(max_w, w + 2))


def _normalise_rows(table: Sequence[Sequence]) -> List[List]:
    """Drop fully empty rows/columns and pad ragged rows."""
    rows = [list(r) for r in table if r and any(c not in (None, "") for c in r)]
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [None] * (width - len(r)) for r in rows]
    keep = [i for i in range(width) if any(r[i] not in (None, "") for r in rows)]
    return [[r[i] for i in keep] for r in rows]


def _extract_tables(page) -> List[List[List]]:
    """Try ruled-line detection first, then text-alignment detection."""
    strategies = (
        {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
        {"vertical_strategy": "text", "horizontal_strategy": "text",
         "snap_tolerance": 3, "join_tolerance": 3, "intersection_tolerance": 5},
    )
    for settings in strategies:
        try:
            tables = page.extract_tables(table_settings=settings)
        except Exception as exc:  # pragma: no cover - pdfplumber edge cases
            logger.debug("Table strategy %s failed: %s", settings, exc)
            continue
        cleaned = [_normalise_rows(t) for t in tables]
        # Text strategy yields false positives; require >=2 rows and >=2 cols.
        cleaned = [t for t in cleaned if len(t) >= 2 and len(t[0]) >= 2]
        if cleaned:
            return cleaned
    return []


# ----------------------------------------------------------------------------
# Core
# ----------------------------------------------------------------------------
def _convert_one(pdf_path: Path, output_dir: Optional[Path],
                 overwrite: bool, password: Optional[str]) -> ConversionResult:
    res = ConversionResult(pdf=pdf_path)
    try:
        if not pdf_path.is_file():
            raise FileNotFoundError(f"File not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError("Not a .pdf file")

        out_dir = output_dir or pdf_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{pdf_path.stem}.xlsx"
        if out_path.exists() and not overwrite:
            i = 1
            while (out_dir / f"{pdf_path.stem}_{i}.xlsx").exists():
                i += 1
            out_path = out_dir / f"{pdf_path.stem}_{i}.xlsx"

        wb = Workbook()
        summary = wb.active
        summary.title = "Summary"
        text_ws = None
        text_row = 1

        with pdfplumber.open(str(pdf_path), password=password) as pdf:
            res.pages = len(pdf.pages)
            for p_no, page in enumerate(pdf.pages, start=1):
                try:
                    tables = _extract_tables(page)
                    for t_no, rows in enumerate(tables, start=1):
                        ws = wb.create_sheet(_unique_sheet_name(wb, f"P{p_no}_T{t_no}"))
                        _write_table(ws, rows)
                        res.tables += 1

                    if not tables:  # fall back to plain text for this page
                        text = (page.extract_text() or "").strip()
                        if not text:
                            res.empty_pages.append(p_no)
                            continue
                        if text_ws is None:
                            text_ws = wb.create_sheet("Text")
                            for c, h in enumerate(("Page", "Line", "Text"), 1):
                                cell = text_ws.cell(row=1, column=c, value=h)
                                cell.fill, cell.font = _HEADER_FILL, _HEADER_FONT
                            text_row = 2
                        for ln, line in enumerate(text.splitlines(), start=1):
                            text_ws.cell(row=text_row, column=1, value=p_no)
                            text_ws.cell(row=text_row, column=2, value=ln)
                            text_ws.cell(row=text_row, column=3, value=_ILLEGAL_XML.sub("", line))
                            text_row += 1
                        res.text_pages += 1
                except Exception as exc:
                    logger.warning("%s page %d skipped: %s", pdf_path.name, p_no, exc)
                    res.empty_pages.append(p_no)
                finally:
                    page.flush_cache()  # keep memory flat on large PDFs

        if text_ws is not None:
            text_ws.column_dimensions["A"].width = 8
            text_ws.column_dimensions["B"].width = 8
            text_ws.column_dimensions["C"].width = 120
            text_ws.freeze_panes = "A2"

        info = [
            ("Source file", str(pdf_path)),
            ("Total pages", res.pages),
            ("Tables extracted", res.tables),
            ("Pages exported as text", res.text_pages),
            ("Pages with no extractable text",
             ", ".join(map(str, res.empty_pages)) or "None"),
        ]
        if res.empty_pages:
            info.append(("Note", "Pages with no text are likely scanned images; run OCR first."))
        for r, (k, v) in enumerate(info, start=1):
            a, b = summary.cell(row=r, column=1, value=k), summary.cell(row=r, column=2, value=v)
            a.font, a.fill = _HEADER_FONT, _HEADER_FILL
            b.alignment = Alignment(wrap_text=True, vertical="top")
        summary.column_dimensions["A"].width = 34
        summary.column_dimensions["B"].width = 80

        wb.save(out_path)
        res.xlsx, res.success = out_path, True
        logger.info("Converted %s", pdf_path.name)
    except PermissionError:
        res.error = "Permission denied (is the output .xlsx open in Excel?)"
    except Exception as exc:
        res.error = f"{type(exc).__name__}: {exc}"
        logger.exception("Failed to convert %s", pdf_path)
    return res


def pdf_to_excel(
    pdf_paths: Union[PathLike, Iterable[PathLike]],
    output_dir: Optional[PathLike] = None,
    overwrite: bool = True,
    password: Optional[str] = None,
) -> List[ConversionResult]:
    """
    Convert one or many PDFs to Excel.

    pdf_paths  : a path or a list of paths.
    output_dir : where to write .xlsx files (default: next to each PDF).
    overwrite  : False -> never replace an existing file (adds _1, _2 ...).
    password   : for encrypted PDFs.

    Returns a list of ConversionResult (never raises for a single bad file,
    so one failure does not stop the batch).
    """
    if isinstance(pdf_paths, (str, Path)):
        pdf_paths = [pdf_paths]
    out = Path(output_dir) if output_dir else None
    return [_convert_one(Path(p), out, overwrite, password) for p in pdf_paths]


# ----------------------------------------------------------------------------
# Entry points
# ----------------------------------------------------------------------------
def _setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
    )
    logging.getLogger("pdfminer").setLevel(logging.ERROR)


if __name__ == "__main__":
    _setup_logging()

    if len(sys.argv) > 1:  # command-line mode
        ap = argparse.ArgumentParser(description="Convert PDF files to Excel")
        ap.add_argument("pdfs", nargs="+")
        ap.add_argument("--out", help="output directory")
        ap.add_argument("--password")
        ap.add_argument("-v", "--verbose", action="store_true")
        a = ap.parse_args()
        _setup_logging(a.verbose)
        results = pdf_to_excel(a.pdfs, a.out, password=a.password)
    else:  # edit this list
        results = pdf_to_excel([
            r"C:\Users\ce\Downloads\phpcheatsheet.pdf",
            # r"C:\Users\ce\Downloads\another_file.pdf",
        ])

    for r in results:
        print(r)
    sys.exit(0 if all(r.success for r in results) else 1)
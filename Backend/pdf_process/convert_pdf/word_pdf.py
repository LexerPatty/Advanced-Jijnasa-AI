from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional, Union

log = logging.getLogger("word_to_pdf")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
    )

WORD_EXTS = (".docx", ".doc", ".docm", ".rtf")
PathLike = Union[str, os.PathLike]


# --------------------------------------------------------------------------- #
# Result object
# --------------------------------------------------------------------------- #
@dataclass
class ConvertResult:
    source: str
    pdf: Optional[str] = None
    ok: bool = False
    error: Optional[str] = None
    engine: Optional[str] = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _resolve_source(p: PathLike) -> Path:
    """Accept paths with or without extension (e.g. '...\\33000000048-4.')."""
    raw = str(p).strip().strip('"').strip("'")
    path = Path(raw)
    if path.is_file() and path.suffix.lower() in WORD_EXTS:
        return path.resolve()

    # No / trailing-dot / wrong extension -> try appending known Word extensions
    stem = raw.rstrip(".")
    for ext in WORD_EXTS:
        cand = Path(stem + ext)
        if cand.is_file():
            return cand.resolve()
    if path.is_file():
        raise ValueError(f"Not a Word file: {path}")
    raise FileNotFoundError(f"File not found: {raw}")


def _out_path(src: Path, out_dir: Optional[Path]) -> Path:
    target_dir = out_dir if out_dir else src.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    return (target_dir / (src.stem + ".pdf")).resolve()


# --------------------------------------------------------------------------- #
# Engine 1: MS Word (COM)
# --------------------------------------------------------------------------- #
class _WordEngine:
    name = "msword"

    def __init__(self):
        import pythoncom  # noqa
        import win32com.client  # noqa

        self._pythoncom = pythoncom
        pythoncom.CoInitialize()
        # DispatchEx => always a private Word instance (won't hijack user's open Word)
        self.app = win32com.client.DispatchEx("Word.Application")
        self.app.Visible = False
        self.app.DisplayAlerts = 0  # wdAlertsNone

    def convert(self, src: Path, dst: Path):
        doc = None
        try:
            doc = self.app.Documents.Open(
                str(src),
                ReadOnly=True,
                AddToRecentFiles=False,
                ConfirmConversions=False,
                NoEncodingDialog=True,
            )
            doc.SaveAs2(str(dst), FileFormat=17)  # 17 = wdFormatPDF
        finally:
            if doc is not None:
                doc.Close(SaveChanges=0)

    def close(self):
        try:
            self.app.Quit(SaveChanges=0)
        finally:
            self._pythoncom.CoUninitialize()


# --------------------------------------------------------------------------- #
# Engine 2: LibreOffice
# --------------------------------------------------------------------------- #
def _find_soffice() -> Optional[str]:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if exe:
        return exe
    for c in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ):
        if os.path.exists(c):
            return c
    return None


class _LibreOfficeEngine:
    name = "libreoffice"

    def __init__(self):
        self.exe = _find_soffice()
        if not self.exe:
            raise RuntimeError("LibreOffice (soffice) not found")
        # isolated profile => safe for parallel / service use
        self._profile = tempfile.mkdtemp(prefix="lo_profile_")

    def convert(self, src: Path, dst: Path):
        with tempfile.TemporaryDirectory(prefix="lo_out_") as tmp:
            cmd = [
                self.exe,
                f"-env:UserInstallation={Path(self._profile).as_uri()}",
                "--headless", "--norestore", "--convert-to", "pdf",
                "--outdir", tmp, str(src),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            produced = Path(tmp) / (src.stem + ".pdf")
            if proc.returncode != 0 or not produced.exists():
                raise RuntimeError(f"LibreOffice failed: {proc.stderr.strip() or proc.stdout.strip()}")
            if dst.exists():
                dst.unlink()
            shutil.move(str(produced), str(dst))

    def close(self):
        shutil.rmtree(self._profile, ignore_errors=True)


def _make_engine(prefer: str = "auto"):
    errors = []
    order = {"auto": ("word", "libre"), "word": ("word",), "libreoffice": ("libre",)}[prefer]
    for kind in order:
        try:
            if kind == "word":
                if platform.system() != "Windows":
                    raise RuntimeError("MS Word engine needs Windows")
                return _WordEngine()
            return _LibreOfficeEngine()
        except Exception as e:  # noqa
            errors.append(f"{kind}: {e}")
    raise RuntimeError("No conversion engine available -> " + " | ".join(errors))


# --------------------------------------------------------------------------- #
# Merge (optional)
# --------------------------------------------------------------------------- #
def merge_pdfs(pdf_paths: Iterable[PathLike], output: PathLike) -> str:
    from pypdf import PdfWriter

    writer = PdfWriter()
    for p in pdf_paths:
        writer.append(str(p))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        writer.write(f)
    writer.close()
    return str(output)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def convert_to_pdf(
    files: Union[PathLike, Iterable[PathLike]],
    output_dir: Optional[PathLike] = None,
    merge_into: Optional[PathLike] = None,
    engine: str = "auto",          # "auto" | "word" | "libreoffice"
    overwrite: bool = True,
    raise_on_error: bool = False,
) -> dict:
    """
    Convert one or many Word files to PDF (order of the list is preserved).

    files        : a single path or a list of paths (extension optional)
    output_dir   : where PDFs go (default: next to each source file)
    merge_into   : if given, also merge all successful PDFs, in list order, into this file
    Returns      : {"results": [...], "converted": n, "failed": n, "merged": path|None}
    """
    if isinstance(files, (str, os.PathLike)):
        files = [files]
    files = list(files)
    out_dir = Path(output_dir).resolve() if output_dir else None

    results: list[ConvertResult] = []
    eng = None
    try:
        for f in files:
            res = ConvertResult(source=str(f))
            results.append(res)
            try:
                src = _resolve_source(f)
                res.source = str(src)
                if src.name.startswith("~$"):
                    raise ValueError("Temporary Word lock file, skipped")
                dst = _out_path(src, out_dir)
                if dst.exists() and not overwrite:
                    raise FileExistsError(f"Output exists: {dst}")

                if eng is None:                       # lazy start: one engine for whole batch
                    eng = _make_engine(engine)
                    log.info("Using engine: %s", eng.name)

                log.info("Converting: %s", src)
                eng.convert(src, dst)
                if not dst.exists() or dst.stat().st_size == 0:
                    raise RuntimeError("PDF was not created")
                res.pdf, res.ok, res.engine = str(dst), True, eng.name
                log.info("   -> %s", dst)
            except Exception as e:  # noqa - keep batch going
                res.error = f"{type(e).__name__}: {e}"
                log.error("FAILED %s | %s", f, res.error)
                if raise_on_error:
                    raise
    finally:
        if eng is not None:
            try:
                eng.close()
            except Exception as e:  # noqa
                log.warning("Engine cleanup issue: %s", e)

    ok_pdfs = [r.pdf for r in results if r.ok]
    merged = None
    if merge_into and ok_pdfs:
        merged = merge_pdfs(ok_pdfs, merge_into)
        log.info("Merged %d PDFs -> %s", len(ok_pdfs), merged)

    return {
        "results": [asdict(r) for r in results],
        "converted": len(ok_pdfs),
        "failed": len(results) - len(ok_pdfs),
        "merged": merged,
    }


if __name__ == "__main__":
    print(convert_to_pdf([
        r"C:\Users\ce\Downloads\NDA format.docx",          # extension optional (.docx/.doc auto-detected)
        # r"C:\Users\ce\Downloads\another_file.docx",
    ]))

    # Examples:
    # convert_to_pdf([...], output_dir=r"C:\Users\ce\Downloads\pdf_out")
    # convert_to_pdf([...], merge_into=r"C:\Users\ce\Downloads\merged.pdf")
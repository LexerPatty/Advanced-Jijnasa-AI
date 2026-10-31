from __future__ import annotations

import logging
import os
import tempfile
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError

logger = logging.getLogger("pdf_merger")

PathLike = Union[str, os.PathLike]


class PdfMergeError(Exception):
    """Raised when the merge cannot be completed."""


def _validate(path: Path) -> None:
    if not path.exists():
        raise PdfMergeError(f"File not found: {path}")
    if not path.is_file():
        raise PdfMergeError(f"Not a file: {path}")
    if path.suffix.lower() != ".pdf":
        raise PdfMergeError(f"Not a .pdf file: {path}")
    if path.stat().st_size == 0:
        raise PdfMergeError(f"Empty file: {path}")
    with open(path, "rb") as f:
        if b"%PDF-" not in f.read(1024):
            raise PdfMergeError(f"Invalid PDF header: {path}")


def merge_pdf(
    pdf_paths: Union[PathLike, Iterable[PathLike]],
    output_path: Optional[PathLike] = None,
    *,
    add_bookmarks: bool = True,
    password: Optional[str] = None,
    skip_invalid: bool = False,
    overwrite: bool = False,
) -> str:
    """
    Merge PDFs, in the order given, into a single PDF.

    Args:
        pdf_paths:     One path or a list of paths (order is preserved).
        output_path:   Destination file. Default: "merged_<timestamp>.pdf"
                       next to the first input file.
        add_bookmarks: Add one bookmark per source file (named after the file).
        password:      Password to try for encrypted inputs.
        skip_invalid:  If True, log and skip bad files instead of aborting.
        overwrite:     Allow replacing an existing output file.

    Returns:
        Absolute path of the merged PDF (str).

    Raises:
        PdfMergeError on any validation / merge failure.
    """
    if isinstance(pdf_paths, (str, os.PathLike)):
        pdf_paths = [pdf_paths]
    paths = [Path(p).expanduser().resolve() for p in pdf_paths]
    if not paths:
        raise PdfMergeError("No input PDF files provided.")

    if output_path is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = paths[0].parent / f"merged_{stamp}.pdf"
    else:
        out = Path(output_path).expanduser().resolve()
    if out.suffix.lower() != ".pdf":
        raise PdfMergeError(f"Output must be a .pdf file: {out}")
    if out.exists() and not overwrite:
        raise PdfMergeError(f"Output exists (use overwrite=True): {out}")
    if out in paths:
        raise PdfMergeError("Output file cannot also be an input file.")
    out.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()
    merged_files = 0
    total_pages = 0

    with ExitStack() as stack:
        for path in paths:
            try:
                _validate(path)
                handle = stack.enter_context(open(path, "rb"))
                reader = PdfReader(handle)
                if reader.is_encrypted:
                    if not password or not reader.decrypt(password):
                        raise PdfMergeError(f"Encrypted, password missing/wrong: {path}")
                n = len(reader.pages)
                if n == 0:
                    raise PdfMergeError(f"PDF has no pages: {path}")
                writer.append(reader, outline_item=path.stem if add_bookmarks else None)
            except (PdfMergeError, PyPdfError, OSError) as exc:
                if skip_invalid:
                    logger.warning("Skipping %s: %s", path, exc)
                    continue
                if isinstance(exc, PdfMergeError):
                    raise
                raise PdfMergeError(f"Failed to read {path}: {exc}") from exc
            merged_files += 1
            total_pages += n
            logger.info("Added %s (%d pages)", path.name, n)

        if merged_files == 0:
            raise PdfMergeError("No valid PDFs to merge.")

        writer.add_metadata({"/Producer": "pdf_merger", "/Title": out.stem})

        # Atomic write: temp file in same folder, then replace.
        fd, tmp_name = tempfile.mkstemp(suffix=".tmp", dir=out.parent)
        try:
            with os.fdopen(fd, "wb") as tmp:
                writer.write(tmp)
            os.replace(tmp_name, out)
        except Exception as exc:
            try:
                os.remove(tmp_name)
            except OSError:
                pass
            raise PdfMergeError(f"Failed to write output {out}: {exc}") from exc

    logger.info("Merged %d files / %d pages -> %s", merged_files, total_pages, out)
    return str(out)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(merge_pdf([
        r"C:\Users\ce\Downloads\phpcheatsheet.pdf",
        r"C:\Users\ce\Downloads\Joydip-Ghosh-Resume.pdf",
    ]))
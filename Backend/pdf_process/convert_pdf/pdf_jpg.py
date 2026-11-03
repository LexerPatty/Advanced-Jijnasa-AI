from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence, Union

import pymupdf as fitz  # PyMuPDF (new import name; avoids deprecation warning)

logger = logging.getLogger("pdf_to_jpg")

PathLike = Union[str, os.PathLike]

MAX_PIXELS_PER_PAGE = 100_000_000  # safety guard against decompression-bomb PDFs


@dataclass
class PdfResult:
    """Outcome for one input PDF."""
    source: str
    success: bool
    output_dir: str | None = None
    images: list[str] = field(default_factory=list)
    pages_total: int = 0
    failed_pages: list[int] = field(default_factory=list)
    error: str | None = None


def _safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip() or "document"


def _convert_one(
    pdf_path: Path,
    output_dir: Path | None,
    dpi: int,
    quality: int,
    password: str | None,
    overwrite: bool,
) -> PdfResult:
    result = PdfResult(source=str(pdf_path), success=False)
    try:
        if not pdf_path.is_file():
            raise FileNotFoundError(f"File not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {pdf_path.name}")

        stem = _safe_name(pdf_path.stem)
        out = (output_dir / stem) if output_dir else pdf_path.parent / f"{stem}_jpg"
        out.mkdir(parents=True, exist_ok=True)
        result.output_dir = str(out)

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        with fitz.open(pdf_path) as doc:
            if doc.needs_pass:
                if not password or not doc.authenticate(password):
                    raise PermissionError("PDF is password protected (missing/incorrect password)")
            result.pages_total = doc.page_count
            if doc.page_count == 0:
                raise ValueError("PDF has no pages")

            width_digits = max(3, len(str(doc.page_count)))
            for idx in range(doc.page_count):
                target = out / f"{stem}_page_{idx + 1:0{width_digits}d}.jpg"
                try:
                    if target.exists() and not overwrite:
                        result.images.append(str(target))
                        continue

                    page = doc.load_page(idx)
                    rect = page.rect
                    if rect.width * zoom * rect.height * zoom > MAX_PIXELS_PER_PAGE:
                        raise ValueError("page too large for requested DPI")

                    # alpha=False -> white background (JPG has no transparency)
                    pix = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)

                    # atomic write: temp file then rename, so no half-written JPGs
                    tmp = target.with_suffix(".jpg.tmp")
                    pix.save(str(tmp), output="jpg", jpg_quality=quality)
                    os.replace(tmp, target)
                    result.images.append(str(target))
                except Exception as page_err:  # keep going on a bad page
                    logger.error("%s page %d failed: %s", pdf_path.name, idx + 1, page_err)
                    result.failed_pages.append(idx + 1)

        result.success = not result.failed_pages and bool(result.images)
        if result.failed_pages:
            result.error = f"{len(result.failed_pages)} page(s) failed: {result.failed_pages}"
        logger.info("%s -> %d image(s)", pdf_path.name, len(result.images))
    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"
        logger.error("%s failed: %s", pdf_path, result.error)
    return result


def pdf_to_jpg(
    pdf_paths: Union[PathLike, Sequence[PathLike]],
    output_dir: PathLike | None = None,
    dpi: int = 200,
    quality: int = 90,
    password: str | None = None,
    overwrite: bool = True,
    max_workers: int = 1,
) -> list[PdfResult]:
    """
    Convert one or more PDFs to JPG images (one JPG per page).

    pdf_paths   : a single path or a list of paths (order is preserved in results)
    output_dir  : root output folder; default = next to each PDF
    dpi         : render resolution (150 = web, 200 = good, 300 = print/OCR)
    quality     : JPG quality 1-100
    password    : password for encrypted PDFs
    overwrite   : re-render existing images
    max_workers : parallel PDFs (1 = sequential)

    Returns a list of PdfResult, one per input, in the same order.
    """
    if isinstance(pdf_paths, (str, os.PathLike)):
        pdf_paths = [pdf_paths]
    paths = [Path(p) for p in pdf_paths]
    if not paths:
        raise ValueError("No PDF paths provided")
    if not 36 <= dpi <= 600:
        raise ValueError("dpi must be between 36 and 600")
    if not 1 <= quality <= 100:
        raise ValueError("quality must be between 1 and 100")

    out_root = Path(output_dir) if output_dir else None

    def job(p: Path) -> PdfResult:
        return _convert_one(p, out_root, dpi, quality, password, overwrite)

    if max_workers > 1 and len(paths) > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            return list(ex.map(job, paths))
    return [job(p) for p in paths]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    pdf_list = [
        r"C:\Users\ce\Downloads\phpcheatsheet.pdf",
        # r"C:\Users\ce\Downloads\another.pdf",
    ]

    for r in pdf_to_jpg(pdf_list, dpi=200, quality=90):
        print(r)
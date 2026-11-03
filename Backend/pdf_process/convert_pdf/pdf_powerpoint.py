from __future__ import annotations

import io
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import fitz  # PyMuPDF
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Pt

logger = logging.getLogger("pdf_to_pptx")

EMU_PER_POINT = 12700  # 1 PDF point = 1/72 inch = 12700 EMU
MAX_SLIDE_EMU = 51206400  # PowerPoint's hard limit (56 inches)
VALID_MODES = ("image", "editable")


@dataclass
class ConversionResult:
    source: str
    output: Optional[str]
    pages: int
    success: bool
    error: Optional[str] = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _emu(points: float) -> Emu:
    return Emu(int(round(points * EMU_PER_POINT)))


def _slide_size_for(page_rect: fitz.Rect) -> tuple[int, int]:
    """Slide size (EMU) matching the first page, capped to PowerPoint's limit."""
    w, h = page_rect.width * EMU_PER_POINT, page_rect.height * EMU_PER_POINT
    scale = min(1.0, MAX_SLIDE_EMU / max(w, h))
    return int(w * scale), int(h * scale)


def _fit(page_w: float, page_h: float, slide_w: int, slide_h: int):
    """Scale + offset to fit a page inside the slide, preserving aspect ratio."""
    scale = min(slide_w / (page_w * EMU_PER_POINT), slide_h / (page_h * EMU_PER_POINT))
    off_x = (slide_w - page_w * EMU_PER_POINT * scale) / 2
    off_y = (slide_h - page_h * EMU_PER_POINT * scale) / 2
    return scale, off_x, off_y


def _blank_slide(prs: Presentation):
    layout = prs.slide_layouts[6]  # blank layout
    return prs.slides.add_slide(layout)


def _set_notes(slide, text: str) -> None:
    text = text.strip()
    if text:
        slide.notes_slide.notes_text_frame.text = text


# --------------------------------------------------------------------------- #
# Page renderers
# --------------------------------------------------------------------------- #
def _add_page_as_image(prs, page: fitz.Page, dpi: int) -> None:
    slide_w, slide_h = prs.slide_width, prs.slide_height
    scale, off_x, off_y = _fit(page.rect.width, page.rect.height, slide_w, slide_h)

    pix = page.get_pixmap(dpi=dpi, alpha=False)
    stream = io.BytesIO(pix.tobytes("png"))

    slide = _blank_slide(prs)
    slide.shapes.add_picture(
        stream,
        Emu(int(off_x)),
        Emu(int(off_y)),
        Emu(int(page.rect.width * EMU_PER_POINT * scale)),
        Emu(int(page.rect.height * EMU_PER_POINT * scale)),
    )
    _set_notes(slide, page.get_text("text"))


def _add_page_as_editable(prs, page: fitz.Page) -> None:
    slide_w, slide_h = prs.slide_width, prs.slide_height
    scale, off_x, off_y = _fit(page.rect.width, page.rect.height, slide_w, slide_h)
    slide = _blank_slide(prs)

    def to_slide(x: float, y: float) -> tuple[int, int]:
        return (
            int(off_x + x * EMU_PER_POINT * scale),
            int(off_y + y * EMU_PER_POINT * scale),
        )

    data = page.get_text("dict")
    for block in data.get("blocks", []):
        # Embedded raster image
        if block.get("type") == 1:
            try:
                x0, y0, x1, y1 = block["bbox"]
                left, top = to_slide(x0, y0)
                width = int((x1 - x0) * EMU_PER_POINT * scale)
                height = int((y1 - y0) * EMU_PER_POINT * scale)
                slide.shapes.add_picture(
                    io.BytesIO(block["image"]), Emu(left), Emu(top), Emu(width), Emu(height)
                )
            except Exception as exc:  # unsupported image encodings
                logger.debug("Skipped an image block: %s", exc)
            continue

        # Text block: one text box per line keeps positioning accurate
        for line in block.get("lines", []):
            spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
            if not spans:
                continue
            x0, y0, x1, y1 = line["bbox"]
            left, top = to_slide(x0, y0)
            width = int((x1 - x0) * EMU_PER_POINT * scale) + EMU_PER_POINT * 4
            height = int((y1 - y0) * EMU_PER_POINT * scale)

            box = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
            tf = box.text_frame
            tf.word_wrap = False
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            para = tf.paragraphs[0]

            for span in spans:
                run = para.add_run()
                run.text = span["text"]
                font = run.font
                font.size = Pt(max(1.0, span["size"] * scale))
                font.name = span.get("font", "Calibri").split("+")[-1].split("-")[0] or "Calibri"
                flags = span.get("flags", 0)
                font.bold = bool(flags & 16)
                font.italic = bool(flags & 2)
                rgb = span.get("color", 0)
                font.color.rgb = RGBColor((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def pdf_to_pptx(
    pdf_path: str | Path,
    output_path: str | Path | None = None,
    mode: str = "image",
    dpi: int = 200,
    password: str | None = None,
) -> str:
    """Convert a single PDF to PPTX and return the output file path."""
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}, got {mode!r}")
    if not 72 <= dpi <= 600:
        raise ValueError("dpi must be between 72 and 600")

    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    output = Path(output_path) if output_path else pdf_path.with_suffix(".pptx")
    output.parent.mkdir(parents=True, exist_ok=True)

    with fitz.open(pdf_path) as doc:
        if doc.needs_pass and not doc.authenticate(password or ""):
            raise PermissionError(f"PDF is password protected: {pdf_path.name}")
        if doc.page_count == 0:
            raise ValueError(f"PDF has no pages: {pdf_path.name}")

        prs = Presentation()
        prs.slide_width, prs.slide_height = (
            Emu(v) for v in _slide_size_for(doc[0].rect)
        )

        for index, page in enumerate(doc, start=1):
            if mode == "image":
                _add_page_as_image(prs, page, dpi)
            else:
                _add_page_as_editable(prs, page)
            logger.info("%s: page %d/%d done", pdf_path.name, index, doc.page_count)

        prs.core_properties.title = (doc.metadata or {}).get("title") or pdf_path.stem
        prs.core_properties.author = (doc.metadata or {}).get("author") or ""
        pages = doc.page_count

    prs.save(output)
    logger.info("Saved %s (%d slides)", output, pages)
    return str(output)


def convert_pdfs(
    pdf_paths: Iterable[str | Path],
    output_dir: str | Path | None = None,
    mode: str = "image",
    dpi: int = 200,
    password: str | None = None,
) -> list[ConversionResult]:
    """
    Convert a list of PDFs. One failing file never stops the batch.
    If output_dir is None, each .pptx is saved next to its source PDF.
    """
    results: list[ConversionResult] = []
    for pdf in pdf_paths:
        pdf = Path(pdf)
        out = Path(output_dir) / f"{pdf.stem}.pptx" if output_dir else None
        try:
            saved = pdf_to_pptx(pdf, out, mode=mode, dpi=dpi, password=password)
            with fitz.open(pdf) as d:
                if d.needs_pass:
                    d.authenticate(password or "")
                n = d.page_count
            results.append(ConversionResult(str(pdf), saved, n, True))
        except Exception as exc:
            logger.error("Failed to convert %s: %s", pdf, exc)
            results.append(ConversionResult(str(pdf), None, 0, False, str(exc)))
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )

    # Add your PDF paths here, in order
    pdf_files = [
        r"C:\Users\ce\Downloads\phpcheatsheet.pdf",
        # r"C:\Users\ce\Downloads\another_file.pdf",
    ]

    # mode="image"    -> exact look of the PDF (recommended for production)
    # mode="editable" -> native, editable text boxes and pictures
    results = convert_pdfs(
        pdf_files,
        output_dir=None,  # e.g. r"C:\Users\ce\Downloads\pptx_output"
        mode="image",
        dpi=200,
    )

    for r in results:
        status = "OK  " if r.success else "FAIL"
        print(f"[{status}] {r.source} -> {r.output or r.error} ({r.pages} pages)")

    sys.exit(0 if all(r.success for r in results) else 1)
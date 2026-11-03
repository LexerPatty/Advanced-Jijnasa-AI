from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Union

from PIL import Image, ImageOps

logger = logging.getLogger("image_to_pdf")

PathLike = Union[str, os.PathLike]
SUPPORTED_EXTS = (".jpg", ".jpeg", ".png")
DPI = 300          # output resolution; controls physical page size
JPEG_QUALITY = 95  # quality used when embedding images into the PDF


class ImageToPdfError(Exception):
    """Raised for any user-facing conversion problem."""


# --------------------------------------------------------------------------- #
# Path handling
# --------------------------------------------------------------------------- #
def _resolve_path(raw: PathLike) -> Path:
    """
    Turn whatever the user typed into a real image file.

    Handles:
      * exact file path                      -> used as is
      * path with missing extension / a
        trailing dot (e.g. '...\\33000000048-4.')  -> tries .jpg/.jpeg/.png
    """
    p = Path(str(raw).strip().strip('"').strip("'"))

    if p.is_file():
        if p.suffix.lower() not in SUPPORTED_EXTS:
            raise ImageToPdfError(f"Unsupported file type: {p}")
        return p

    # Try appending extensions (case-insensitive) to the given path.
    base = str(p).rstrip(".")
    for ext in SUPPORTED_EXTS:
        for candidate in (base + ext, base + ext.upper()):
            if Path(candidate).is_file():
                return Path(candidate)

    # Case-insensitive match inside the parent folder (Windows is already
    # case-insensitive, but Linux/macOS are not).
    parent = p.parent
    if parent.is_dir():
        stem = Path(base).name.lower()
        for f in parent.iterdir():
            if not (f.is_file() and f.suffix.lower() in SUPPORTED_EXTS):
                continue
            if f.stem.lower() == stem or f.name.lower() == p.name.lower():
                return f

    raise ImageToPdfError(f"Image not found: {raw}")


def _normalise_inputs(paths: Union[PathLike, Iterable[PathLike]]) -> list[Path]:
    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]
    resolved = [_resolve_path(p) for p in paths]
    if not resolved:
        raise ImageToPdfError("No input images were provided.")
    return resolved


# --------------------------------------------------------------------------- #
# Image handling
# --------------------------------------------------------------------------- #
def _load_as_rgb(path: Path) -> Image.Image:
    """Open an image, fix orientation, flatten transparency onto white."""
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)  # honour phone/scanner rotation
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                rgba = im.convert("RGBA")
                background = Image.new("RGB", rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.getchannel("A"))
                return background
            return im.convert("RGB")  # also handles CMYK, L, P, 16-bit, etc.
    except ImageToPdfError:
        raise
    except Exception as exc:
        raise ImageToPdfError(f"Cannot read image '{path}': {exc}") from exc


def _default_output(first_image: Path) -> Path:
    name = first_image.stem.rstrip(".") or "output"
    return first_image.with_name(f"{name}.pdf")


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def merge_pdf(
    paths: Union[PathLike, Iterable[PathLike]],
    output_pdf: PathLike | None = None,
    overwrite: bool = True,
) -> Path:
    """
    Convert JPG/PNG image(s) into one PDF (one image per page, in list order).

    Args:
        paths:      A single path or a list of paths, in the order you want
                    the pages.
        output_pdf: Where to save the PDF. Defaults to the first image's
                    folder, named after the first image.
        overwrite:  If False, raise instead of replacing an existing PDF.

    Returns:
        Path of the created PDF.
    """
    images = _normalise_inputs(paths)
    out = Path(output_pdf) if output_pdf else _default_output(images[0])

    if out.exists() and not overwrite:
        raise ImageToPdfError(f"Output already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Converting %d image(s) -> %s", len(images), out)
    pages = [_load_as_rgb(p) for p in images]

    # Write to a temp file first, then atomically replace, so a crash never
    # leaves a half-written/corrupt PDF behind.
    fd, tmp_name = tempfile.mkstemp(suffix=".pdf", dir=out.parent)
    os.close(fd)
    try:
        pages[0].save(
            tmp_name,
            format="PDF",
            save_all=True,
            append_images=pages[1:],
            resolution=float(DPI),
            quality=JPEG_QUALITY,
        )
        os.replace(tmp_name, out)
    except Exception as exc:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise ImageToPdfError(f"Failed to write PDF '{out}': {exc}") from exc
    finally:
        for p in pages:
            p.close()

    logger.info("PDF created: %s", out)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        # ---- EDIT HERE: list the images in the page order you want ----
        result = merge_pdf([
            r"C:\Users\ce\Downloads\img 1 1.jpg",      # extension optional
            # r"C:\Users\ce\Downloads\33000000048-5.jpg",
            # r"C:\Users\ce\Downloads\33000000048-6.png",
        ])
        print(f"Saved: {result}")
    except ImageToPdfError as e:
        logger.error("%s", e)
        sys.exit(1)
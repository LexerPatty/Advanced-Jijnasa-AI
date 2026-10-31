"""
pdf_compressor.py - Enterprise-grade PDF compressor (iLovePDF-style levels).

Engine : Ghostscript (the same engine most commercial PDF tools use).
Install: Windows -> https://ghostscript.com/releases/gsdnld.html  (64-bit installer)
         Linux   -> apt install ghostscript
         macOS   -> brew install ghostscript
         Optional: set env var GS_PATH to the gs executable if it is not auto-detected.
Python : pip install pypdf

Levels
    extreme      Less quality, high compression   (72 dpi images,  low JPEG quality)
    recommended  Good quality, good compression   (150 dpi images, medium JPEG quality)
    less         High quality, less compression   (300 dpi images, high JPEG quality)

Usage
    from pdf_compressor import compress_pdf
    result = compress_pdf(r"C:\\Users\\ce\\Downloads\\file.pdf", level="recommended")
    print(result)
"""
from __future__ import annotations

import enum
import glob
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from pypdf import PdfReader
from pypdf.errors import PyPdfError

logger = logging.getLogger("pdf_compressor")

PathLike = Union[str, os.PathLike]


class PdfCompressError(Exception):
    """Raised when compression cannot be completed."""


class CompressionLevel(str, enum.Enum):
    EXTREME = "extreme"          # Less quality, high compression
    RECOMMENDED = "recommended"  # Good quality, good compression
    LESS = "less"                # High quality, less compression


@dataclass(frozen=True)
class _Profile:
    preset: str      # Ghostscript -dPDFSETTINGS baseline
    dpi: int         # target image resolution
    qfactor: float   # JPEG quality factor (lower = better quality, bigger file)


_PROFILES = {
    CompressionLevel.EXTREME:     _Profile("/screen",  72, 1.30),
    CompressionLevel.RECOMMENDED: _Profile("/ebook",  150, 0.76),
    CompressionLevel.LESS:        _Profile("/printer", 300, 0.40),
}


@dataclass(frozen=True)
class CompressionResult:
    output_path: str
    level: str
    original_size: int
    compressed_size: int
    pages: int
    already_optimal: bool  # True -> compression could not shrink it; original kept

    @property
    def saved_bytes(self) -> int:
        return self.original_size - self.compressed_size

    @property
    def reduction_percent(self) -> float:
        if self.original_size == 0:
            return 0.0
        return round(100.0 * self.saved_bytes / self.original_size, 2)

    def __str__(self) -> str:
        note = " (already optimal, original kept)" if self.already_optimal else ""
        return (
            f"{self.output_path}\n"
            f"  level: {self.level} | pages: {self.pages}\n"
            f"  {_fmt(self.original_size)} -> {_fmt(self.compressed_size)} "
            f"(-{self.reduction_percent}%){note}"
        )


def _fmt(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return f"{n} B"


def find_ghostscript() -> str:
    """Locate the Ghostscript executable (env GS_PATH > PATH > common install dirs)."""
    env = os.environ.get("GS_PATH")
    if env:
        if Path(env).is_file():
            return env
        raise PdfCompressError(f"GS_PATH is set but not a file: {env}")

    names = ["gswin64c", "gswin32c", "gs"] if sys.platform == "win32" else ["gs"]
    for name in names:
        found = shutil.which(name)
        if found:
            return found

    if sys.platform == "win32":
        patterns = []
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if base:
                patterns.append(os.path.join(base, "gs", "gs*", "bin", "gswin64c.exe"))
                patterns.append(os.path.join(base, "gs", "gs*", "bin", "gswin32c.exe"))
        for pattern in patterns:
            matches = sorted(glob.glob(pattern), reverse=True)  # newest version first
            if matches:
                return matches[0]

    raise PdfCompressError(
        "Ghostscript not found. Install it (https://ghostscript.com) or set the "
        "GS_PATH environment variable to the gs executable."
    )


def _validate_input(path: Path, password: Optional[str]) -> int:
    """Validate the input PDF and return its page count."""
    if not path.exists():
        raise PdfCompressError(f"File not found: {path}")
    if not path.is_file():
        raise PdfCompressError(f"Not a file: {path}")
    if path.suffix.lower() != ".pdf":
        raise PdfCompressError(f"Not a .pdf file: {path}")
    if path.stat().st_size == 0:
        raise PdfCompressError(f"Empty file: {path}")
    try:
        with open(path, "rb") as fh:
            reader = PdfReader(fh)
            if reader.is_encrypted:
                if not password:
                    raise PdfCompressError(f"PDF is password protected (pass password=...): {path}")
                if not reader.decrypt(password):
                    raise PdfCompressError(f"Wrong password: {path}")
            pages = len(reader.pages)
    except PyPdfError as exc:
        raise PdfCompressError(f"Invalid or corrupt PDF {path}: {exc}") from exc
    if pages == 0:
        raise PdfCompressError(f"PDF has no pages: {path}")
    return pages


def _build_command(gs: str, profile: _Profile, src: Path, dst: str,
                   password: Optional[str]) -> list:
    q = profile.qfactor
    dict_ps = (
        f"<< /QFactor {q} /Blend 1 /HSamples [2 1 1 2] /VSamples [2 1 1 2] >>"
    )
    setparams = (
        f"<< /ColorImageDict {dict_ps} /GrayImageDict {dict_ps} "
        f"/AutoFilterColorImages false /AutoFilterGrayImages false "
        f"/ColorImageFilter /DCTEncode /GrayImageFilter /DCTEncode >> setdistillerparams"
    )
    cmd = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.5",
        f"-dPDFSETTINGS={profile.preset}",
        "-dNOPAUSE", "-dBATCH", "-dQUIET", "-dSAFER",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        "-dDownsampleColorImages=true", "-dDownsampleGrayImages=true",
        "-dDownsampleMonoImages=true",
        "-dColorImageDownsampleType=/Bicubic",
        "-dGrayImageDownsampleType=/Bicubic",
        "-dMonoImageDownsampleType=/Subsample",
        f"-dColorImageResolution={profile.dpi}",
        f"-dGrayImageResolution={profile.dpi}",
        f"-dMonoImageResolution={max(profile.dpi, 150) * 2}",
        f"-sOutputFile={dst}",
    ]
    if password:
        cmd.append(f"-sPDFPassword={password}")
    # -c ... -f must come last: PostScript to set JPEG quality, then the input file.
    cmd += ["-c", setparams, "-f", str(src)]
    return cmd


# Pure-Python engine settings: (max image long edge in px, JPEG quality)
_PY_PROFILES = {
    CompressionLevel.EXTREME:     (900, 30),
    CompressionLevel.RECOMMENDED: (1600, 60),
    CompressionLevel.LESS:        (2600, 80),
}


def _compress_with_python(src: Path, dst: str, lvl: CompressionLevel,
                          password: Optional[str]) -> None:
    """Fallback engine (no Ghostscript): recompress images with Pillow + pypdf."""
    try:
        from PIL import Image
    except ImportError:
        raise PdfCompressError(
            "Ghostscript not found and Pillow is missing. "
            "Install Ghostscript or run: pip install pillow"
        ) from None

    max_edge, quality = _PY_PROFILES[lvl]
    try:
        from pypdf import PdfWriter
        reader = PdfReader(str(src))
        if reader.is_encrypted:
            reader.decrypt(password or "")
        writer = PdfWriter(clone_from=reader)
        for page in writer.pages:
            try:
                images = list(page.images)
            except Exception as exc:  # unreadable resources: leave page as is
                logger.warning("Could not read images on a page: %s", exc)
                images = []
            for img in images:
                try:
                    pil = img.image
                    if pil is None or pil.mode not in ("RGB", "L"):
                        continue  # skip alpha / palette / CMYK images (kept untouched)
                    scale = max_edge / max(pil.size)
                    if scale < 1:
                        pil = pil.resize(
                            (max(1, int(pil.width * scale)), max(1, int(pil.height * scale))),
                            Image.LANCZOS,
                        )
                    img.replace(pil, quality=quality)
                except Exception as exc:
                    logger.debug("Skipping an image: %s", exc)
            try:
                page.compress_content_streams()
            except Exception:
                pass
        writer.compress_identical_objects()
        with open(dst, "wb") as fh:
            writer.write(fh)
    except PdfCompressError:
        raise
    except Exception as exc:
        raise PdfCompressError(f"Python compression engine failed: {exc}") from exc


def compress_pdf(
    input_path: PathLike,
    level: Union[CompressionLevel, str] = CompressionLevel.RECOMMENDED,
    output_path: Optional[PathLike] = None,
    *,
    password: Optional[str] = None,
    overwrite: bool = False,
    keep_original_if_larger: bool = True,
    timeout: int = 600,
    engine: str = "auto",
) -> CompressionResult:
    """
    Compress a PDF at one of three levels.

    Args:
        input_path: PDF to compress.
        level:      "extreme" | "recommended" | "less" (or CompressionLevel).
        output_path: Destination. Default: "<name>_compressed_<level>.pdf" beside the input.
        password:   Password for encrypted input (output is not encrypted).
        overwrite:  Allow replacing an existing output file.
        keep_original_if_larger: If compression does not shrink the file, deliver a copy
                    of the original instead (never returns a bigger file).
        timeout:    Seconds before Ghostscript is killed.
        engine:     "auto" (Ghostscript if installed, else built-in Python engine),
                    "ghostscript" (require it) or "python" (force built-in engine).

    Returns:
        CompressionResult (sizes, reduction %, output path).

    Raises:
        PdfCompressError on any failure.
    """
    try:
        lvl = CompressionLevel(level.lower() if isinstance(level, str) else level)
    except ValueError:
        valid = ", ".join(l.value for l in CompressionLevel)
        raise PdfCompressError(f"Invalid level {level!r}. Choose one of: {valid}") from None

    src = Path(input_path).expanduser().resolve()
    pages = _validate_input(src, password)

    out = (Path(output_path).expanduser().resolve() if output_path
           else src.with_name(f"{src.stem}_compressed_{lvl.value}.pdf"))
    if out.suffix.lower() != ".pdf":
        raise PdfCompressError(f"Output must be a .pdf file: {out}")
    if out == src:
        raise PdfCompressError("Output file cannot be the same as the input file.")
    if out.exists() and not overwrite:
        raise PdfCompressError(f"Output exists (use overwrite=True): {out}")
    out.parent.mkdir(parents=True, exist_ok=True)

    engine = engine.lower()
    if engine not in ("auto", "ghostscript", "python"):
        raise PdfCompressError("engine must be 'auto', 'ghostscript' or 'python'")
    gs = None
    if engine in ("auto", "ghostscript"):
        try:
            gs = find_ghostscript()
        except PdfCompressError:
            if engine == "ghostscript":
                raise
            logger.warning("Ghostscript not found; using built-in Python engine "
                           "(lower compression). Install Ghostscript for best results.")
    original_size = src.stat().st_size

    fd, tmp_name = tempfile.mkstemp(suffix=".tmp", dir=out.parent)
    os.close(fd)
    try:
        logger.info("Compressing %s (%s, %s, engine=%s)", src.name, lvl.value,
                    _fmt(original_size), "ghostscript" if gs else "python")
        if gs is None:
            _compress_with_python(src, tmp_name, lvl, password)
        else:
            cmd = _build_command(gs, _PROFILES[lvl], src, tmp_name, password)
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # no console flash
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=timeout, check=False, **kwargs)
            except subprocess.TimeoutExpired:
                raise PdfCompressError(f"Ghostscript timed out after {timeout}s: {src}") from None
            except OSError as exc:
                raise PdfCompressError(f"Could not run Ghostscript: {exc}") from exc

            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout or "").strip()[:500]
                raise PdfCompressError(f"Ghostscript failed (exit {proc.returncode}): {detail}")

        # Verify the produced file is a readable PDF with the same page count.
        try:
            with open(tmp_name, "rb") as fh:
                out_pages = len(PdfReader(fh).pages)
        except (PyPdfError, OSError) as exc:
            raise PdfCompressError(f"Compressed output is invalid: {exc}") from exc
        if out_pages != pages:
            raise PdfCompressError(
                f"Page count mismatch after compression ({pages} -> {out_pages}); aborted."
            )

        new_size = os.path.getsize(tmp_name)
        already_optimal = False
        if keep_original_if_larger and new_size >= original_size:
            shutil.copyfile(src, tmp_name)
            new_size = original_size
            already_optimal = True

        os.replace(tmp_name, out)  # atomic publish
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass

    result = CompressionResult(str(out), lvl.value, original_size, new_size, pages,
                               already_optimal)
    logger.info("Done: %s -> %s (-%s%%)", _fmt(original_size), _fmt(new_size),
                result.reduction_percent)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # level: "extreme" | "recommended" | "less"
    print(compress_pdf(r"C:\Users\ce\Downloads\phpcheatsheet.pdf", level="recommended"))
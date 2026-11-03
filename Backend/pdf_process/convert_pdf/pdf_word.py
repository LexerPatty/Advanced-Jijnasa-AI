
from __future__ import annotations

import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional

from pdf2docx import Converter

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger("pdf_to_word")


def _setup_logging(log_file: Optional[Path] = None) -> None:
    """Configure console (+ optional file) logging once."""
    if logger.handlers:
        return
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)


# --------------------------------------------------------------------------- #
# Result model
# --------------------------------------------------------------------------- #
@dataclass
class ConversionResult:
    source: str
    output: Optional[str]
    success: bool
    error: Optional[str]
    seconds: float


# --------------------------------------------------------------------------- #
# Core single-file conversion (top-level so it is picklable for multiprocessing)
# --------------------------------------------------------------------------- #
def _convert_one(
    pdf_path: str,
    output_dir: Optional[str],
    overwrite: bool,
    password: Optional[str],
    start_page: int,
    end_page: Optional[int],
) -> dict:
    started = time.perf_counter()
    src = Path(pdf_path)

    def fail(msg: str) -> dict:
        return asdict(
            ConversionResult(
                str(src), None, False, msg, round(time.perf_counter() - started, 2)
            )
        )

    # ---- validation ----
    if not src.exists():
        return fail("File not found")
    if not src.is_file():
        return fail("Path is not a file")
    if src.suffix.lower() != ".pdf":
        return fail("Not a .pdf file")
    if src.stat().st_size == 0:
        return fail("File is empty")

    out_dir = Path(output_dir) if output_dir else src.parent
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return fail(f"Cannot create output directory: {exc}")

    dest = out_dir / f"{src.stem}.docx"
    if dest.exists() and not overwrite:
        # never clobber silently: add a numeric suffix
        n = 1
        while (out_dir / f"{src.stem}_{n}.docx").exists():
            n += 1
        dest = out_dir / f"{src.stem}_{n}.docx"

    # ---- conversion ----
    cv = None
    try:
        cv = Converter(str(src), password=password) if password else Converter(str(src))
        cv.convert(str(dest), start=start_page, end=end_page)
    except Exception as exc:  # pdf2docx raises many exception types
        # remove half-written output
        try:
            if dest.exists():
                dest.unlink()
        except OSError:
            pass
        return fail(f"{type(exc).__name__}: {exc}")
    finally:
        if cv is not None:
            try:
                cv.close()
            except Exception:
                pass

    return asdict(
        ConversionResult(
            str(src), str(dest), True, None, round(time.perf_counter() - started, 2)
        )
    )


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def convert_pdfs_to_word(
    pdf_paths: Iterable[str],
    output_dir: Optional[str] = None,
    overwrite: bool = False,
    password: Optional[str] = None,
    start_page: int = 0,
    end_page: Optional[int] = None,
    workers: int = 1,
    log_file: Optional[str] = None,
) -> list[dict]:
    """
    Convert one or more PDF files to Word (.docx).

    Parameters
    ----------
    pdf_paths   : list of PDF file paths (a single string is also accepted).
    output_dir  : folder for the .docx files. Default: same folder as each PDF.
    overwrite   : replace an existing .docx (default False -> adds _1, _2 ...).
    password    : password for encrypted PDFs (applied to all files).
    start_page  : first page to convert (0-based).
    end_page    : last page (exclusive). None = to the end.
    workers     : parallel processes. 1 = sequential (safest). Use 2-4 for big batches.
    log_file    : optional path to write a persistent log.

    Returns
    -------
    List of dicts: source, output, success, error, seconds.
    """
    _setup_logging(Path(log_file) if log_file else None)

    if isinstance(pdf_paths, (str, Path)):
        pdf_paths = [str(pdf_paths)]
    paths = [str(p) for p in pdf_paths]

    if not paths:
        logger.warning("No input files supplied.")
        return []

    logger.info("Starting conversion of %d file(s)", len(paths))
    results: list[dict] = []

    def _log(res: dict) -> None:
        if res["success"]:
            logger.info("OK     %s -> %s (%.2fs)", res["source"], res["output"], res["seconds"])
        else:
            logger.error("FAILED %s | %s", res["source"], res["error"])

    args = (output_dir, overwrite, password, start_page, end_page)

    if workers <= 1 or len(paths) == 1:
        for p in paths:
            res = _convert_one(p, *args)
            _log(res)
            results.append(res)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_convert_one, p, *args): p for p in paths}
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                except Exception as exc:
                    res = asdict(
                        ConversionResult(futures[fut], None, False, f"Worker crashed: {exc}", 0.0)
                    )
                _log(res)
                results.append(res)

    ok = sum(r["success"] for r in results)
    logger.info("Done: %d succeeded, %d failed", ok, len(results) - ok)
    return results


# Keep the same call style as your sample: merge_pdf(path) -> convert one file
def pdf_to_word(pdf_path: str, **kwargs) -> list[dict]:
    return convert_pdfs_to_word([pdf_path], **kwargs)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Add as many PDF paths as you like, in list order.
    pdf_files = [
        r"C:\Users\ce\Downloads\phpcheatsheet.pdf",
        # r"C:\Users\ce\Downloads\another_file.pdf",
    ]

    summary = convert_pdfs_to_word(
        pdf_files,
        output_dir=r"C:\Users\ce\Downloads\word_output",  # set to None to save next to each PDF
        overwrite=False,
        workers=1,                                         # raise to 2-4 for large batches
        log_file=r"C:\Users\ce\Downloads\word_output\conversion.log",
    )

    for item in summary:
        print(item)
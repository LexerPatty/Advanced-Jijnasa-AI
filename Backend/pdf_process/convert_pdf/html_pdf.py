"""
html_to_pdf.py  -  Enterprise HTML -> PDF converter (ordered list -> one merged PDF)

 * Accepts http(s) URLs, local paths (Windows or POSIX) and file:// links, in the
   order you want them in the final PDF.
 * BLANK-PAGE PROOF, two layers:
     1. Print-CSS fixes injected before rendering (no trailing page-break, no
        100vh overflow, no empty trailing containers).
     2. Post-render pixel + text analysis of every page; blank pages are deleted.
   A source that renders 100% blank is treated as a failed load and retried.
 * Parallel rendering with preserved order, retries with backoff, lazy-load
   scrolling, image/font wait, atomic output write, bookmarks per source,
   PDF metadata, JSON report, CLI + importable API.

Install:
    pip install playwright pymupdf
    playwright install chromium

Usage (API):
    from html_to_pdf import html_to_pdf
    html_to_pdf([r"C:\\Users\\ce\\Downloads\\a.html", "https://example.com"],
                r"C:\\Users\\ce\\Downloads\\merged.pdf")

Usage (CLI):
    python html_to_pdf.py -o merged.pdf a.html b.html https://example.com
    python html_to_pdf.py -o merged.pdf --list sources.txt
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence
from urllib.parse import urlparse

import pymupdf as fitz  # PyMuPDF
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

log = logging.getLogger("html_to_pdf")


# --------------------------------------------------------------------------- #
# Configuration / result models
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PdfOptions:
    # layout
    page_format: str = "A4"                  # A4 / Letter / Legal ...
    landscape: bool = False
    prefer_css_page_size: bool = True        # honour @page { size: ... } in the HTML
    margin: dict = field(default_factory=lambda: {
        "top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
    print_background: bool = True
    scale: float = 1.0
    viewport_width: int = 1280               # layout width before printing
    # "print"  = use the site's print CSS (many portals HIDE content here)
    # "screen" = look exactly like the browser
    # "auto"   = try print, and if text is missing from the PDF, fall back to screen
    media: str = "auto"
    min_text_coverage: float = 0.6           # PDF must contain >=60% of the page's visible text
    fail_on_low_coverage: bool = False       # True = treat a mostly-empty PDF as a failure

    # page readiness / access
    wait_for_selector: str | None = None     # e.g. "#dashboard" - wait until it is visible
    storage_state_path: str | None = None    # Playwright saved session (cookies/localStorage)
    login: dict | None = None                # form login, see _do_login() docstring
    debug_dir: str | None = None             # saves screenshot + html + console log per source

    # blank-page handling
    remove_blank_pages: bool = True
    blank_pixel_ratio: float = 0.0002        # <0.02% non-background pixels = blank
    blank_color_tolerance: int = 12          # 0-255 grey-level tolerance

    # reliability
    timeout_ms: int = 60_000
    settle_ms: int = 500
    retries: int = 3
    retry_backoff_s: float = 2.0
    concurrency: int = 4
    allow_partial: bool = False              # True = skip failed sources, merge rest
    ignore_https_errors: bool = False        # internal self-signed certs only
    extra_http_headers: dict = field(default_factory=dict)  # e.g. {"Authorization": "..."}

    # output
    add_bookmarks: bool = True
    metadata_title: str | None = None
    metadata_author: str | None = None
    report_path: str | None = None           # write JSON report here if set


@dataclass
class SourceResult:
    index: int
    source: str
    title: str = ""
    pdf_path: str | None = None
    pages_rendered: int = 0
    blank_pages_removed: int = 0
    attempts: int = 0
    final_url: str = ""
    media_used: str = ""
    text_coverage: float = 1.0
    warnings: list = field(default_factory=list)
    error: str | None = None


class ConversionError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# Injected CSS: stops the usual causes of trailing / phantom blank pages
# --------------------------------------------------------------------------- #
_ANTI_BLANK_CSS = """
@media print {
  html, body { height: auto !important; min-height: 0 !important;
               overflow: visible !important; }
  body { margin-bottom: 0 !important; padding-bottom: 0 !important; }
  body > *:last-child, body > *:last-child > *:last-child {
      page-break-after: avoid !important; break-after: avoid !important;
      margin-bottom: 0 !important; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""

_JS_WAIT_IMAGES = """
() => Promise.all(Array.from(document.images).map(img =>
    img.complete ? 1 : new Promise(r => { img.onload = img.onerror = r; })))
"""

_JS_SCROLL = """
async () => {                       // trigger lazy-loaded images / content
  const step = Math.max(300, window.innerHeight);
  for (let y = 0; y < document.body.scrollHeight; y += step) {
    window.scrollTo(0, y);
    await new Promise(r => setTimeout(r, 80));
  }
  window.scrollTo(0, 0);
}
"""

_JS_REMOVE_EMPTY_TAIL = """
() => {                             // drop empty trailing elements that add a page
  const b = document.body; if (!b) return;
  let n = b.lastElementChild;
  while (n && !n.innerText.trim() && !n.querySelector('img,svg,canvas,video,iframe,table,hr,input,button,select,textarea,form')
         && n.tagName !== 'SCRIPT') { const p = n.previousElementSibling; n.remove(); n = p; }
}
"""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _to_url(source: str) -> str:
    source = source.strip().strip('"').strip("'")
    scheme = urlparse(source).scheme.lower()
    if scheme in ("http", "https", "file"):
        return source
    path = Path(source).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"HTML file not found: {source}")
    return path.resolve().as_uri()


def _is_blank(page: "fitz.Page", opts: PdfOptions) -> bool:
    """Blank = no text AND (almost) every pixel equals the background colour."""
    if page.get_text("text").strip():
        return False
    pix = page.get_pixmap(matrix=fitz.Matrix(0.35, 0.35),
                          colorspace=fitz.csGRAY, alpha=False)
    data = pix.samples
    if not data:
        return True
    bg = Counter(data).most_common(1)[0][0]
    tol = opts.blank_color_tolerance
    diff = sum(1 for v in data if abs(v - bg) > tol)
    return (diff / len(data)) < opts.blank_pixel_ratio


def _strip_blank_pages(pdf_path: Path, opts: PdfOptions) -> tuple[int, int]:
    """Delete blank pages in place. Returns (pages_kept, blanks_removed)."""
    doc = fitz.open(pdf_path)
    try:
        total = doc.page_count
        if not opts.remove_blank_pages:
            return total, 0
        blanks = [i for i in range(total) if _is_blank(doc[i], opts)]
        if not blanks:
            return total, 0
        if len(blanks) == total:        # everything blank -> caller will retry/fail
            return 0, total
        doc.delete_pages(blanks)
        tmp = pdf_path.with_suffix(".clean.pdf")
        doc.save(tmp, garbage=3, deflate=True)
    finally:
        doc.close()
    os.replace(tmp, pdf_path)
    return total - len(blanks), len(blanks)


def _pdf_text_len(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as d:
        return sum(len("".join(p.get_text("text").split())) for p in d)


_JS_VISIBLE_TEXT_LEN = """
() => document.body ? document.body.innerText.replace(/\\s/g, '').length : 0
"""


async def _do_login(browser, opts: PdfOptions):
    """Form login once; returns a Playwright storage_state dict reused by every page.

    opts.login = {
        "url": "https://portal.example.com/index.php",
        "fields": {"input[name=username]": "user", "input[name=password]": "pass"},
        "submit": "button[type=submit]",
        "success_selector": "#dashboard",     # optional: wait for this after login
    }
    Tip: read credentials from environment variables, never hard-code them.
    """
    cfg = opts.login
    ctx = await browser.new_context(ignore_https_errors=opts.ignore_https_errors)
    try:
        page = await ctx.new_page()
        page.set_default_timeout(opts.timeout_ms)
        await page.goto(cfg["url"], wait_until="load")
        for selector, value in cfg["fields"].items():
            await page.fill(selector, value)
        await page.click(cfg["submit"])
        if cfg.get("success_selector"):
            await page.wait_for_selector(cfg["success_selector"])
        else:
            await page.wait_for_load_state("networkidle")
        return await ctx.storage_state()
    finally:
        await ctx.close()


async def _render_one(browser, idx: int, source: str, out_pdf: Path,
                      opts: PdfOptions, sem: asyncio.Semaphore,
                      storage_state=None) -> SourceResult:
    res = SourceResult(index=idx, source=source)
    url = _to_url(source)
    async with sem:
        last_err: Exception | None = None
        for attempt in range(1, opts.retries + 1):
            res.attempts = attempt
            res.warnings = []
            context = await browser.new_context(
                ignore_https_errors=opts.ignore_https_errors,
                viewport={"width": opts.viewport_width, "height": 1000},
                extra_http_headers=opts.extra_http_headers or None,
                storage_state=storage_state,
            )
            console: list[str] = []
            try:
                page = await context.new_page()
                page.set_default_timeout(opts.timeout_ms)
                page.on("console", lambda m: console.append(f"console.{m.type}: {m.text}"))
                page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
                page.on("requestfailed", lambda r: console.append(f"requestfailed: {r.url}"))

                resp = await page.goto(url, wait_until="load")
                if resp is not None and resp.status >= 400:
                    raise ConversionError(f"HTTP {resp.status}")
                try:
                    await page.wait_for_load_state("networkidle", timeout=10_000)
                except PlaywrightError:
                    pass
                if opts.wait_for_selector:
                    await page.wait_for_selector(opts.wait_for_selector, state="visible")
                await page.evaluate(_JS_SCROLL)
                await asyncio.wait_for(page.evaluate(_JS_WAIT_IMAGES), opts.timeout_ms / 1000)
                await page.evaluate("document.fonts && document.fonts.ready")
                await page.wait_for_timeout(opts.settle_ms)

                res.final_url = page.url
                res.title = (await page.title()).strip() or Path(urlparse(url).path).stem or url
                if url.startswith("http") and page.url.rstrip("/") != url.rstrip("/"):
                    res.warnings.append(f"redirected to {page.url} (login page?)")

                dom_len = await page.evaluate(_JS_VISIBLE_TEXT_LEN)
                if dom_len < 20:
                    res.warnings.append("page has almost no visible text (login wall / JS not rendered?)")

                if opts.debug_dir:
                    dd = Path(opts.debug_dir); dd.mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path=str(dd / f"{idx + 1:03d}.png"), full_page=True)
                    (dd / f"{idx + 1:03d}.html").write_text(await page.content(), encoding="utf-8")

                await page.evaluate(_JS_REMOVE_EMPTY_TAIL)

                # ---- render; "auto" falls back from print CSS to screen CSS -------------
                modes = ["print", "screen"] if opts.media == "auto" else [opts.media]
                best = None                                  # (coverage, mode, path)
                for mode in modes:
                    await page.emulate_media(media=mode)
                    if mode == "print":
                        await page.add_style_tag(content=_ANTI_BLANK_CSS)
                    cand = out_pdf.with_suffix(f".{mode}.pdf")
                    await page.pdf(
                        path=str(cand),
                        format=opts.page_format,
                        landscape=opts.landscape,
                        print_background=opts.print_background,
                        prefer_css_page_size=opts.prefer_css_page_size,
                        margin=opts.margin,
                        scale=opts.scale,
                    )
                    if not cand.exists() or cand.stat().st_size == 0:
                        raise ConversionError("empty PDF produced")
                    pdf_len = await asyncio.to_thread(_pdf_text_len, cand)
                    cov = min(1.0, pdf_len / dom_len) if dom_len else 1.0
                    log.debug("[%d] media=%s coverage=%.0f%%", idx + 1, mode, cov * 100)
                    if best is None or cov > best[0]:
                        best = (cov, mode, cand)
                    if cov >= opts.min_text_coverage:
                        break
                cov, mode, cand = best
                os.replace(cand, out_pdf)
                res.media_used, res.text_coverage = mode, round(cov, 3)
                if cov < opts.min_text_coverage:
                    msg = (f"PDF contains only {cov:.0%} of the page's visible text - "
                           f"content likely hidden, behind login, or inside a scroll container")
                    if opts.fail_on_low_coverage:
                        raise ConversionError(msg)
                    res.warnings.append(msg)

                kept, removed = await asyncio.to_thread(_strip_blank_pages, out_pdf, opts)
                if kept == 0:
                    raise ConversionError("page rendered completely blank")
                res.pages_rendered, res.blank_pages_removed = kept, removed
                res.pdf_path = str(out_pdf)
                res.error = None
                for w in res.warnings:
                    log.warning("[%d] %s: %s", idx + 1, source, w)
                log.info("[%d] OK  %s  (%d pages, %d blank removed, media=%s, text=%.0f%%)",
                         idx + 1, source, kept, removed, mode, cov * 100)
                if opts.debug_dir:
                    (Path(opts.debug_dir) / f"{idx + 1:03d}.console.txt").write_text(
                        "\n".join(console), encoding="utf-8")
                return res
            except Exception as e:  # noqa: BLE001
                last_err = e
                log.warning("[%d] attempt %d/%d failed: %s -> %s",
                            idx + 1, attempt, opts.retries, source, e)
                if attempt < opts.retries:
                    await asyncio.sleep(opts.retry_backoff_s * 2 ** (attempt - 1))
            finally:
                await context.close()
        res.error = str(last_err)
        return res


async def _convert_all(sources: Sequence[str], tmp: Path, opts: PdfOptions):
    sem = asyncio.Semaphore(max(1, opts.concurrency))
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--disable-dev-shm-usage"])
        try:
            state = opts.storage_state_path
            if opts.login:
                state = await _do_login(browser, opts)
            tasks = [_render_one(browser, i, s, tmp / f"{i:05d}.pdf", opts, sem, state)
                     for i, s in enumerate(sources)]
            return await asyncio.gather(*tasks)      # order == input order
        finally:
            await browser.close()


def _merge(results: list[SourceResult], out: Path, opts: PdfOptions) -> int:
    merged = fitz.open()
    toc, total_pages = [], 0
    try:
        for r in results:
            with fitz.open(r.pdf_path) as part:
                toc.append([1, r.title or Path(r.source).stem, total_pages + 1])
                merged.insert_pdf(part)
                total_pages += part.page_count
        if opts.add_bookmarks:
            merged.set_toc(toc)
        merged.set_metadata({
            "title": opts.metadata_title or "",
            "author": opts.metadata_author or "",
            "producer": "html_to_pdf (Playwright/Chromium + PyMuPDF)",
        })
        fd, tmp_out = tempfile.mkstemp(suffix=".pdf", dir=out.parent)
        os.close(fd)
        try:
            merged.save(tmp_out, garbage=3, deflate=True)
            os.replace(tmp_out, out)          # atomic: never a half-written file
        except Exception:
            Path(tmp_out).unlink(missing_ok=True)
            raise
    finally:
        merged.close()
    return total_pages


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def html_to_pdf(sources: Sequence[str], output_pdf: str,
                options: PdfOptions | None = None) -> str:
    """Convert ordered HTML sources into ONE merged, blank-page-free PDF.
    Returns the absolute output path."""
    opts = options or PdfOptions()
    sources = [s for s in sources if s and s.strip()]
    if not sources:
        raise ValueError("No HTML sources provided")

    out = Path(output_pdf).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()

    with tempfile.TemporaryDirectory(prefix="html2pdf_") as td:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        results = asyncio.run(_convert_all(sources, Path(td), opts))

        failed = [r for r in results if r.error]
        for r in failed:
            log.error("FAILED [%d] %s -> %s", r.index + 1, r.source, r.error)
        if failed and not opts.allow_partial:
            raise ConversionError(
                f"{len(failed)}/{len(sources)} sources failed; nothing written. "
                f"First: {failed[0].source} -> {failed[0].error}")
        good = [r for r in results if not r.error]
        if not good:
            raise ConversionError("All sources failed")

        total_pages = _merge(good, out, opts)

        if opts.report_path:
            Path(opts.report_path).write_text(json.dumps({
                "output": str(out), "total_pages": total_pages,
                "seconds": round(time.time() - started, 2),
                "sources": [asdict(r) for r in results],
            }, indent=2), encoding="utf-8")

    log.info("Done: %d/%d sources, %d pages, %d blank pages removed -> %s (%.1fs)",
             len(good), len(sources), total_pages,
             sum(r.blank_pages_removed for r in good), out, time.time() - started)
    return str(out)


# --------------------------------------------------------------------------- #
# CLI / sample
# --------------------------------------------------------------------------- #
def _cli(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Convert ordered HTML sources to one PDF")
    ap.add_argument("sources", nargs="*", help="URLs or file paths, in order")
    ap.add_argument("--list", help="text file with one source per line")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--landscape", action="store_true")
    ap.add_argument("--format", default="A4")
    ap.add_argument("--keep-blank", action="store_true", help="do not remove blank pages")
    ap.add_argument("--allow-partial", action="store_true")
    ap.add_argument("--report", help="write JSON report to this path")
    ap.add_argument("--log-file")
    a = ap.parse_args(argv)

    srcs = list(a.sources)
    if a.list:
        srcs += [l.strip() for l in Path(a.list).read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.startswith("#")]
    handlers = [logging.StreamHandler()]
    if a.log_file:
        handlers.append(logging.FileHandler(a.log_file, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        print(html_to_pdf(srcs, a.output, PdfOptions(
            landscape=a.landscape, page_format=a.format,
            remove_blank_pages=not a.keep_blank,
            allow_partial=a.allow_partial, report_path=a.report)))
        return 0
    except Exception as e:  # noqa: BLE001
        log.error("%s", e)
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(_cli(sys.argv[1:]))

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    print(html_to_pdf(
        [
            # r"C:\Users\ce\Downloads\33000000048-4.html",   # local file
            # r"C:\Users\ce\Downloads\33000000048-5.html",   # local file
            "https://portal.arodek.com/index.php",               # or a web URL
        ],
        r"C:\Users\ce\Downloads\merged_output.pdf",
        PdfOptions(report_path=r"C:\Users\ce\Downloads\merged_report.json"),
    ))
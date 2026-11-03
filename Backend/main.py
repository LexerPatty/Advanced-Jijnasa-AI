import shutil
import tempfile
from pathlib import Path
import uuid

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import shutil

from pdf_process.convert_pdf.word_pdf import WORD_EXTS, convert_to_pdf

app = FastAPI(title="Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "Backend running"}


# Plain `def` (not async): FastAPI runs it in a worker thread, so the blocking
# Word/LibreOffice conversion doesn't freeze the server.
@app.post("/convert/word-to-pdf")
def word_to_pdf(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    ext = Path(filename).suffix.lower()
    if ext not in WORD_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(WORD_EXTS)}",
        )

    # Word/LibreOffice need real files on disk, so use a temp folder that is
    # wiped the moment this block ends. Nothing is kept after the request.
    with tempfile.TemporaryDirectory(prefix="w2p_") as tmp:
        src_path = Path(tmp) / filename
        with open(src_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = convert_to_pdf(src_path, output_dir=Path(tmp) / "out")["results"][0]
        if not result["ok"]:
            raise HTTPException(status_code=500, detail=result["error"])

        pdf_bytes = Path(result["pdf"]).read_bytes()  # load into memory
    # temp folder is already deleted here

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{Path(filename).stem}.pdf"'
        },
    )



    
# --------------------------------------------------
# SHARE PDF DOWNLOAD
# --------------------------------------------------

SHARED_PDF_DIR = Path("shared_pdfs")
SHARED_PDF_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/convert/word-to-pdf/share")
async def create_share_link(
    request: Request,
    file: UploadFile = File(...)
):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed."
            )

        file_id = str(uuid.uuid4())

        pdf_path = SHARED_PDF_DIR / f"{file_id}.pdf"

        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        PUBLIC_BASE_URL = "http://192.168.1.10:8001"

        download_url = (
            f"{PUBLIC_BASE_URL}/shared/{file_id}"
        )

        return {
            "status": True,
            "message": "Share link generated successfully",
            "download_url": download_url,
            "file_name": file.filename
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------------------------
# DOWNLOAD SHARED PDF
# --------------------------------------------------

@app.get("/shared/{file_id}")
async def download_shared_pdf(file_id: str):

    # Validate UUID
    try:
        uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid download ID"
        )

    pdf_path = SHARED_PDF_DIR / f"{file_id}.pdf"

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found or link expired"
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="converted_document.pdf",
        content_disposition_type="attachment"
    )

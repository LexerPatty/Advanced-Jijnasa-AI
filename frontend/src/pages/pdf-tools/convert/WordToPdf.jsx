import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { renderAsync } from "docx-preview";
import { QRCodeSVG } from "qrcode.react";

import {
  FileText,
  FileType,
  Download,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Loader2,
  X,
  FileUp,
  Home,
  Cloud,
  Share2,
  Copy,
  ExternalLink,
} from "lucide-react";

export default function WordToPdf() {
  const navigate = useNavigate();

  const previewRef = useRef(null);
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [converting, setConverting] = useState(false);

  const [convertedPdf, setConvertedPdf] = useState(null);

  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  // Share modal states
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const [shareLoading, setShareLoading] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  const [processingTime, setProcessingTime] = useState(0);

  const API_URL = "http://localhost:8001/convert/word-to-pdf";

  const SHARE_API_URL =
    "http://localhost:8001/convert/word-to-pdf/share";

  // --------------------------------------------------
  // FILE VALIDATION AND UPLOAD
  // --------------------------------------------------

  const processFile = (selectedFile) => {
    if (!selectedFile) return;

    setError("");

    if (!selectedFile.name.toLowerCase().endsWith(".docx")) {
      setError("Please upload only DOCX files.");
      return;
    }

    if (convertedPdf?.url) {
      URL.revokeObjectURL(convertedPdf.url);
    }

    setFile(selectedFile);
    setConvertedPdf(null);
    setShareUrl("");
    setShareModalOpen(false);
  };

  const handleFileUpload = (event) => {
    const selectedFile = event.target.files?.[0];

    processFile(selectedFile);

    event.target.value = "";
  };

  // --------------------------------------------------
  // DRAG AND DROP
  // --------------------------------------------------

  const handleDragOver = (event) => {
    event.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setDragging(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);

    const droppedFile = event.dataTransfer.files?.[0];

    processFile(droppedFile);
  };

  // --------------------------------------------------
  // GOOGLE DRIVE / DROPBOX
  // --------------------------------------------------


  
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_API_KEY;
const GOOGLE_APP_ID = import.meta.env.VITE_GOOGLE_APP_ID;

// Load Google's JavaScript libraries
const loadGoogleScript = (src) => {
  return new Promise((resolve, reject) => {
    const existingScript = document.querySelector(
      `script[src="${src}"]`
    );

    if (existingScript) {
      // Check whether the Google API is already available
      if (
        src.includes("gsi/client") &&
        window.google?.accounts?.oauth2
      ) {
        resolve();
        return;
      }

      if (
        src.includes("api.js") &&
        window.gapi?.load
      ) {
        resolve();
        return;
      }

      existingScript.addEventListener("load", resolve, {
        once: true,
      });

      existingScript.addEventListener(
        "error",
        () => reject(new Error(`Failed to load script: ${src}`)),
        { once: true }
      );

      return;
    }

    const script = document.createElement("script");

    script.src = src;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      console.log("Script loaded:", src);
      resolve();
    };

    script.onerror = () => {
      reject(new Error(`Failed to load script: ${src}`));
    };

    document.body.appendChild(script);
  });
};

// Google Drive import
const handleImportFromDrive = async () => {
  try {
    setError("");

    console.log("Starting Google Drive import...");

    console.log("Google Client ID:", GOOGLE_CLIENT_ID);
    console.log("Google API Key exists:", Boolean(GOOGLE_API_KEY));
    console.log("Google App ID:", GOOGLE_APP_ID);

    if (!GOOGLE_CLIENT_ID || !GOOGLE_API_KEY || !GOOGLE_APP_ID) {
      throw new Error(
        "Google Drive credentials are missing. Check your .env file."
      );
    }

    // Load Google Identity Services and Google API scripts
    await Promise.all([
      loadGoogleScript(
        "https://accounts.google.com/gsi/client"
      ),
      loadGoogleScript(
        "https://apis.google.com/js/api.js"
      ),
    ]);

    console.log("Google scripts loaded.");

    // Load Google Picker
    await new Promise((resolve, reject) => {
      window.gapi.load("picker", {
        callback: resolve,
        onerror: () =>
          reject(new Error("Google Picker library failed to load.")),
      });
    });

    console.log("Google Picker library loaded.");

    // Initialize OAuth token client
    const tokenClient =
      window.google.accounts.oauth2.initTokenClient({
        client_id: GOOGLE_CLIENT_ID,

        scope:
          "https://www.googleapis.com/auth/drive.readonly",

        callback: async (tokenResponse) => {
          try {
            console.log("OAuth callback received.");

            if (tokenResponse.error) {
              throw new Error(
                tokenResponse.error_description ||
                  tokenResponse.error
              );
            }

            const accessToken =
              tokenResponse.access_token;

            if (!accessToken) {
              throw new Error(
                "Google OAuth did not return an access token."
              );
            }

            console.log("Access token received.");

            // DOCX-only Google Drive view
            // const view =
            //   new window.google.picker.DocsView(
            //     window.google.picker.ViewId.DOCS
            //   );

            // view.setMimeTypes(
            //   "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            // );

            // view.setSelectFolderEnabled(false);


            const view = new window.google.picker.DocsView(
  window.google.picker.ViewId.DOCS
);

view.setSelectFolderEnabled(false);

            // Build Picker
            const picker =
              new window.google.picker.PickerBuilder()
                .addView(view)
                .setOAuthToken(accessToken)
                .setDeveloperKey(GOOGLE_API_KEY)
                .setAppId(GOOGLE_APP_ID)
                .setOrigin(window.location.protocol + "//" + window.location.host)
                .setTitle("Select a Word document")
                .setCallback(async (data) => {
                  console.log("Picker callback:", data);

                  if (
                    data.action !==
                    window.google.picker.Action.PICKED
                  ) {
                    return;
                  }

                  try {
                    const selectedFile = data.docs[0];

                    console.log(
                      "Selected Google Drive file:",
                      selectedFile.name
                    );

                    
const GOOGLE_DOCS_MIME =
  "application/vnd.google-apps.document";

const DOCX_MIME =
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

const isGoogleDoc =
  selectedFile.mimeType === GOOGLE_DOCS_MIME;

const downloadUrl = isGoogleDoc
  ? `https://www.googleapis.com/drive/v3/files/${selectedFile.id}/export?mimeType=${encodeURIComponent(DOCX_MIME)}`
  : `https://www.googleapis.com/drive/v3/files/${selectedFile.id}?alt=media`;

const response = await fetch(downloadUrl, {
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
});

if (!response.ok) {
  const responseText = await response.text();

  console.error("Drive download error:", responseText);

  throw new Error(
    "Unable to download the selected Google Drive file."
  );
}

const blob = await response.blob();

const importedFile = new File(
  [blob],
  selectedFile.name.replace(/\.(docx|doc)$/i, "") + ".docx",
  {
    type: DOCX_MIME,
  }
);

processFile(importedFile);


                    console.log(
                      "Google Drive file imported successfully."
                    );
                  } catch (err) {
                    console.error(
                      "Google Drive file import error:",
                      err
                    );

                    setError(
                      err.message ||
                        "Unable to import the Google Drive file."
                    );
                  }
                })
                .build();

            console.log("Opening Google Picker...");

            picker.setVisible(true);
          } catch (err) {
            console.error(
              "Google Picker initialization error:",
              err
            );

            setError(
              err.message ||
                "Google Drive Picker failed to open."
            );
          }
        },
      });

    console.log("Requesting Google OAuth access token...");

    tokenClient.requestAccessToken({
      prompt: "consent",
    });
  } catch (err) {
    console.error(
      "Google Drive import error:",
      err
    );

    setError(
      err.message ||
        "Unable to connect to Google Drive."
    );
  }
};


  const handleSaveToDrive = () => {
    setError(
      "Google Drive save integration is not configured yet."
    );
  };

  const handleSaveToDropbox = () => {
    setError(
      "Dropbox save integration is not configured yet."
    );
  };

  // --------------------------------------------------
  // DOCX PREVIEW
  // --------------------------------------------------

  useEffect(() => {
    if (!file || !previewRef.current) return;

    let cancelled = false;

    const renderPreview = async () => {
      try {
        setPreviewLoading(true);

        previewRef.current.innerHTML = "";

        await renderAsync(
          file,
          previewRef.current,
          undefined,
          {
            className: "docx-preview",
            inWrapper: true,
            ignoreWidth: false,
            ignoreHeight: false,
            breakPages: true,
            useBase64URL: true,
          }
        );
      } catch (err) {
        console.error("Preview error:", err);

        if (!cancelled) {
          setError(
            "Unable to preview this DOCX file. You can still convert it."
          );
        }
      } finally {
        if (!cancelled) {
          setPreviewLoading(false);
        }
      }
    };

    renderPreview();

    return () => {
      cancelled = true;
    };
  }, [file]);



  useEffect(() => {
  let interval;

  if (converting) {
    interval = setInterval(() => {
      setProcessingTime((prev) => prev + 100);
    }, 100);
  }

  return () => clearInterval(interval);
}, [converting]);

  // --------------------------------------------------
  // CONVERT DOCX TO PDF
  // --------------------------------------------------

  const handleConvert = async () => {
    if (!file) {
      setError("Please upload a DOCX file first.");
      return;
    }

    setConverting(true);
    setError("");
    setShareUrl("");

    if (convertedPdf?.url) {
      URL.revokeObjectURL(convertedPdf.url);
    }

    setConvertedPdf(null);

    try {
      const formData = new FormData();

      formData.append("file", file);

      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = "Conversion failed.";

        try {
          const errorData = await response.json();

          errorMessage =
            errorData.detail ||
            errorData.message ||
            errorMessage;
        } catch {
          // Ignore non-JSON errors
        }

        throw new Error(errorMessage);
      }

      const pdfBlob = await response.blob();

      if (pdfBlob.size === 0) {
        throw new Error("The generated PDF file is empty.");
      }

      const pdfUrl = URL.createObjectURL(pdfBlob);

      setConvertedPdf({
        url: pdfUrl,
        blob: pdfBlob,
        name: file.name.replace(/\.docx$/i, ".pdf"),
      });
    } catch (err) {
      console.error("Conversion error:", err);

      setError(
        err.message ||
          "Something went wrong while converting the document."
      );
    } finally {
      setConverting(false);
    }
  };

  // --------------------------------------------------
  // DOWNLOAD PDF
  // --------------------------------------------------

  const handleDownload = () => {
    if (!convertedPdf) return;

    const link = document.createElement("a");

    link.href = convertedPdf.url;
    link.download = convertedPdf.name;

    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  // --------------------------------------------------
  // SHARE DOWNLOAD LINK
  // --------------------------------------------------

  const handleShareDownloadLink = async () => {
    if (!convertedPdf?.blob) {
      setError("Please convert the document first.");
      return;
    }

    setShareLoading(true);
    setError("");

    try {
      const formData = new FormData();

      formData.append(
        "file",
        convertedPdf.blob,
        convertedPdf.name
      );

      const response = await fetch(SHARE_API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = "Unable to generate share link.";

        try {
          const errorData = await response.json();

          errorMessage =
            errorData.detail ||
            errorData.message ||
            errorMessage;
        } catch {
          // Ignore non-JSON errors
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      if (!data.download_url) {
        throw new Error(
          "Download URL was not returned by the server."
        );
      }

      setShareUrl(data.download_url);
      setShareModalOpen(true);
    } catch (err) {
      console.error("Share link error:", err);

      setError(
        err.message ||
          "Unable to generate the download link."
      );
    } finally {
      setShareLoading(false);
    }
  };

  // --------------------------------------------------
  // COPY SHARE LINK
  // --------------------------------------------------

  const handleCopyShareLink = async () => {
    if (!shareUrl) return;

    try {
      await navigator.clipboard.writeText(shareUrl);

      setCopySuccess(true);

      setTimeout(() => {
        setCopySuccess(false);
      }, 2000);
    } catch (err) {
      console.error("Copy error:", err);

      setError("Unable to copy the download link.");
    }
  };

  // --------------------------------------------------
  // REMOVE FILE
  // --------------------------------------------------

  const handleRemoveFile = () => {
    if (convertedPdf?.url) {
      URL.revokeObjectURL(convertedPdf.url);
    }

    setFile(null);
    setConvertedPdf(null);

    setError("");
    setPreviewLoading(false);

    setShareModalOpen(false);
    setShareUrl("");
    setCopySuccess(false);

    if (previewRef.current) {
      previewRef.current.innerHTML = "";
    }

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  // --------------------------------------------------
  // CLEANUP
  // --------------------------------------------------

  useEffect(() => {
    return () => {
      if (convertedPdf?.url) {
        URL.revokeObjectURL(convertedPdf.url);
      }
    };
  }, [convertedPdf]);

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <main className="h-screen overflow-hidden bg-[#f5f7ff] text-slate-800">

      {/* MAIN CONTENT */}

      <div className="flex h-[calc(103vh-40px)] flex-col px-3 py-2 sm:px-5">

        {/* TITLE */}

        <section className="mb-2 mt-4 flex shrink-0 items-center justify-between">

          <div className="flex items-center gap-2">

            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
              <FileType size={20} />
            </div>

            <div>
              <h1 className="text-lg font-extrabold tracking-tight special_heading sm:text-2xl">
                Word to PDF
              </h1>

              <p className="text-[10px] text-slate-500 sm:text-xs">
                Convert DOCX documents into PDF files
              </p>
            </div>

          </div>

          <button
            onClick={() => navigate("/dashboard")}
            title="Go to Dashboard"
            className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-xl border border-blue-100 bg-blue-50 text-blue-600 transition hover:bg-blue-600 hover:text-white"
          >
            <Home size={18} />
          </button>

        </section>

        {/* ERROR */}

        {error && (
          <div className="mb-2 flex shrink-0 items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600">

            <AlertCircle size={15} />

            <span className="flex-1">{error}</span>

            <button
              onClick={() => setError("")}
              className="cursor-pointer"
            >
              <X size={15} />
            </button>

          </div>
        )}

        {/* LEFT / RIGHT CONTAINERS */}

        <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 overflow-hidden lg:grid-cols-[40fr_60fr] mt-3 ">

          {/* LEFT PANEL */}

          <section className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-4">

            {/* LEFT HEADER */}

            <div className="mb-3 shrink-0">

              <h2 className="text-xl font-bold text-slate-800 special_heading">
                Upload Document
              </h2>

              <p className="mt-0.5 text-[10px] text-slate-500 sm:text-xs">
                Select or drop a Word document to convert
              </p>

            </div>

            {/* UPLOAD AREA */}

            {!file ? (

              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={`flex min-h-0 flex-1 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-4 text-center transition ${
                  dragging
                    ? "border-blue-600 bg-blue-100"
                    : "border-blue-200 bg-blue-50/50 hover:border-blue-500 hover:bg-blue-50"
                }`}
              >

                <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-blue-600">
                  <FileUp size={28} />
                </div>

                <h3 className="text-sm font-bold text-slate-700">
                  {dragging
                    ? "Drop your DOCX file here"
                    : "Drag & Drop your file"}
                </h3>

                <p className="mt-1 text-[10px] text-slate-500 sm:text-xs">
                  Or click to browse from your device
                </p>

                <span className="mt-3 rounded-md bg-white px-3 py-1.5 text-[10px] font-bold text-blue-600 shadow-sm">
                  DOCX ONLY
                </span>

                {/* DIVIDER */}

                <div className="my-4 flex w-full max-w-[220px] items-center gap-3">

                  <div className="h-px flex-1 bg-slate-200" />

                  <span className="text-[10px] font-medium text-slate-400">
                    OR IMPORT FROM
                  </span>

                  <div className="h-px flex-1 bg-slate-200" />

                </div>

                {/* GOOGLE DRIVE AND DROPBOX */}

                <div className="flex items-center justify-center gap-5">

                  {/* GOOGLE DRIVE */}

                  <button
                type="button"
                onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();

                    console.log("Google Drive button clicked");

                    handleImportFromDrive();
                }}
                title="Select Word from Google Drive"
                className="group flex flex-col items-center gap-2"
                >

                    <div className="flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white shadow-sm transition group-hover:-translate-y-1 group-hover:border-blue-300 group-hover:shadow-md">

                      <svg
                        width="24"
                        height="24"
                        viewBox="0 0 87.3 78"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path fill="#0066DA" d="M29.5 0h28.3L87.3 50H59z" />
                        <path fill="#00AC47" d="M29.5 0 0 50l14.2 24.6L43.7 24.6z" />
                        <path fill="#EA4335" d="M14.2 74.6h59L87.3 50H28.3z" />
                        <path fill="#00832D" d="M0 50h28.3l15.4-25.4H29.5z" />
                        <path fill="#2684FC" d="M59 0H29.5l14.2 24.6H59z" />
                        <path fill="#FFBA00" d="M59 24.6 43.7 50h28.3L87.3 50z" />
                      </svg>

                    </div>

                    <span className="text-[10px] font-semibold text-slate-600">
                      Google Drive
                    </span>

                  </button>

                  {/* DROPBOX */}

                  <button
                    type="button"
                    onClick={() =>
                      setError(
                        "Dropbox import integration is not configured yet."
                      )
                    }
                    title="Select Word from Dropbox"
                    className="group flex flex-col items-center gap-2"
                  >

                    <div className="flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white shadow-sm transition group-hover:-translate-y-1 group-hover:border-blue-300 group-hover:shadow-md">

                      <svg
                        width="25"
                        height="25"
                        viewBox="0 0 24 24"
                        fill="#0061FF"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path d="M6 1L0 5l6 4 6-4-6-4z" />
                        <path d="M18 1l-6 4 6 4 6-4-6-4z" />
                        <path d="M6 9l-6 4 6 4 6-4-6-4z" />
                        <path d="M18 9l-6 4 6 4 6-4-6-4z" />
                        <path d="M6 18l6-4 6 4-6 4-6-4z" />
                      </svg>

                    </div>

                    <span className="text-[10px] font-semibold text-slate-600">
                      Dropbox
                    </span>

                  </button>

                </div>

                <input
                  ref={inputRef}
                  type="file"
                  accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleFileUpload}
                  className="hidden"
                />

              </div>

            ) : (

              /* FILE UPLOADED */

              <div className="flex min-h-0 flex-1 flex-col justify-center rounded-xl border border-blue-200 bg-blue-50/60 p-4">

                <div className="flex items-center justify-between">

                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                    <FileText size={25} />
                  </div>

                  <button
                    onClick={handleRemoveFile}
                    title="Remove file"
                    className="cursor-pointer rounded-lg p-1.5 text-slate-400 hover:bg-red-100 hover:text-red-600"
                  >
                    <X size={16} />
                  </button>

                </div>

                <h3 className="mt-3 break-all text-xs font-bold text-slate-800 sm:text-sm">
                  {file.name}
                </h3>

                <p className="mt-1 text-[10px] text-slate-500">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>

                <div className="mt-3 flex items-center gap-1.5 text-[10px] font-bold text-emerald-600 sm:text-xs">
                  <CheckCircle size={14} />
                  File Uploaded
                </div>

                <label className="mt-3 flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-blue-200 bg-white px-3 py-2 text-xs font-semibold text-blue-600 transition hover:bg-blue-100">

                  <RefreshCw size={14} />
                  Change File

                  <input
                    type="file"
                    accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    onChange={handleFileUpload}
                    className="hidden"
                  />

                </label>

              </div>

            )}

            {/* CONVERSION DETAILS */}

            

<div className="mt-3 shrink-0 rounded-xl bg-slate-50 p-3">

  <h3 className="text-xs font-bold text-slate-700">
    Conversion Details
  </h3>

  <div className="mt-3 space-y-3 text-[10px] sm:text-xs">

    {/* Input → Output */}
    <div className="flex items-center justify-between">
      <span className="text-slate-500">Input → Output</span>

      <div className="flex items-center gap-2 font-semibold">
        <span className="text-slate-700">DOCX</span>
        <span className="text-blue-500">→</span>
        <span className="text-slate-700">PDF</span>
      </div>
    </div>

    {/* Status */}
    <div className="flex items-center justify-between">
      <span className="text-slate-500">Status</span>

      <span
        className={`flex items-center gap-1.5 font-semibold ${
          convertedPdf
            ? "text-emerald-600"
            : converting
            ? "text-blue-600"
            : "text-slate-400"
        }`}
      >
        {converting && (
          <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
        )}

        {convertedPdf
          ? "Completed"
          : converting
          ? "Processing"
          : "Waiting"}
      </span>
    </div>

    {/* Processing Time */}
    <div className="flex items-center justify-between">
      <span className="text-slate-500">Processing Time</span>

      <span className="font-mono font-semibold text-slate-700">
        {(processingTime / 1000).toFixed(1)} sec
      </span>
    </div>

  </div>

</div>



          </section>

          {/* RIGHT PANEL */}

          <section className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

            {/* PREVIEW HEADER */}

            <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-3 py-3 sm:px-4">

              <div>

                <h2 className="text-xl font-bold text-slate-800 special_heading">
                  Document Preview
                </h2>

                <p className="text-[10px] text-slate-500 sm:text-xs">
                  Preview before converting
                </p>

              </div>

              {file && (
                <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-bold text-emerald-600">
                  <CheckCircle size={12} />
                  Loaded
                </span>
              )}

            </div>

            {/* PREVIEW AREA */}

            <div className="relative min-h-0 flex-1 overflow-hidden bg-slate-100 p-2 sm:p-3">

              {!file ? (

                <div className="flex h-full flex-col items-center justify-center text-center">

                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-slate-300 shadow-sm">
                    <FileText size={32} />
                  </div>

                  <h3 className="mt-3 text-sm font-bold text-slate-600">
                    No Document Preview
                  </h3>

                  <p className="mt-1 max-w-xs text-[10px] leading-5 text-slate-400 sm:text-xs">
                    Upload a DOCX file to preview it here.
                  </p>

                </div>

              ) : (

                <>

                  {previewLoading && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80">

                      <div className="text-center">

                        <Loader2
                          size={28}
                          className="mx-auto animate-spin text-blue-600"
                        />

                        <p className="mt-2 text-xs font-semibold text-slate-600">
                          Loading preview...
                        </p>

                      </div>

                    </div>
                  )}

                  <div
                    ref={previewRef}
                    className="docx-preview-container h-full overflow-auto rounded-lg bg-white shadow-sm"
                  />

                </>
              )}

            </div>

            {/* CONVERT / DOWNLOAD */}

            <div className="shrink-0 border-t border-slate-200 bg-white p-3 sm:p-4">

              {!convertedPdf ? (

                <button
                  type="button"
                  onClick={handleConvert}
                  disabled={!file || converting}
                  className={`flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-bold text-white transition ${
                    !file || converting
                      ? "cursor-not-allowed bg-slate-300"
                      : "bg-gradient-to-r from-blue-600 to-indigo-600 shadow-md shadow-blue-100 hover:-translate-y-0.5 hover:shadow-lg"
                  }`}
                >

                  {converting ? (
                    <>
                      <Loader2 size={17} className="animate-spin" />
                      Converting...
                    </>
                  ) : (
                    <>
                      <FileType size={17} />
                      Convert to PDF
                    </>
                  )}

                </button>

              ) : (

                <div className="space-y-3">

                  {/* COMPLETED MESSAGE */}

                  <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-2.5">

                    <CheckCircle
                      size={20}
                      className="shrink-0 text-emerald-600"
                    />

                    <div className="min-w-0 flex-1">

                      <h3 className="text-xs font-bold text-emerald-700">
                        Conversion Completed!
                      </h3>

                      <p className="truncate text-[10px] text-emerald-600">
                        {convertedPdf.name}
                      </p>

                    </div>

                  </div>

                  {/* DOWNLOAD PDF */}

                  <button
                    type="button"
                    onClick={handleDownload}
                    className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-3 text-sm font-bold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
                  >
                    <Download size={17} />
                    Download PDF
                  </button>

                  {/* THREE ROUND ACTION BUTTONS */}

                  <div className="flex items-center justify-center gap-6 pt-1">

                    {/* GOOGLE DRIVE */}

                    <button
                      type="button"
                      onClick={handleSaveToDrive}
                      title="Save to Google Drive"
                      className="group flex flex-col items-center gap-2"
                    >

                      <div className="flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white shadow-sm transition group-hover:-translate-y-1 group-hover:border-blue-300 group-hover:shadow-md">

                        <svg
                          width="24"
                          height="24"
                          viewBox="0 0 87.3 78"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path fill="#0066DA" d="M29.5 0h28.3L87.3 50H59z" />
                          <path fill="#00AC47" d="M29.5 0 0 50l14.2 24.6L43.7 24.6z" />
                          <path fill="#EA4335" d="M14.2 74.6h59L87.3 50H28.3z" />
                          <path fill="#00832D" d="M0 50h28.3l15.4-25.4H29.5z" />
                          <path fill="#2684FC" d="M59 0H29.5l14.2 24.6H59z" />
                          <path fill="#FFBA00" d="M59 24.6 43.7 50h28.3L87.3 50z" />
                        </svg>

                      </div>

                      <span className="text-[10px] font-semibold text-slate-600">
                        Save to Drive
                      </span>

                    </button>

                    {/* DROPBOX */}

                    <button
                      type="button"
                      onClick={handleSaveToDropbox}
                      title="Save to Dropbox"
                      className="group flex flex-col items-center gap-2"
                    >

                      <div className="flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white shadow-sm transition group-hover:-translate-y-1 group-hover:border-blue-300 group-hover:shadow-md">

                        <svg
                          width="25"
                          height="25"
                          viewBox="0 0 24 24"
                          fill="#0061FF"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path d="M6 1L0 5l6 4 6-4-6-4z" />
                          <path d="M18 1l-6 4 6 4 6-4-6-4z" />
                          <path d="M6 9l-6 4 6 4 6-4-6-4z" />
                          <path d="M18 9l-6 4 6 4 6-4-6-4z" />
                          <path d="M6 18l6-4 6 4-6 4-6-4z" />
                        </svg>

                      </div>

                      <span className="text-[10px] font-semibold text-slate-600">
                        Save to Dropbox
                      </span>

                    </button>

                    {/* SHARE DOWNLOAD LINK */}

                    <button
                      type="button"
                      onClick={handleShareDownloadLink}
                      disabled={shareLoading}
                      title="Share Download Link"
                      className="group flex flex-col items-center gap-2"
                    >

                      <div className="flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white text-blue-600 shadow-sm transition group-hover:-translate-y-1 group-hover:border-blue-300 group-hover:shadow-md">

                        {shareLoading ? (
                          <Loader2
                            size={22}
                            className="animate-spin"
                          />
                        ) : (
                          <Share2 size={22} />
                        )}

                      </div>

                      <span className="text-[10px] font-semibold text-slate-600">
                        Share Link
                      </span>

                    </button>

                  </div>

                  {/* CONVERT AGAIN */}

                  <button
                    type="button"
                    onClick={handleConvert}
                    disabled={converting}
                    className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
                  >

                    <RefreshCw size={13} />
                    Convert Again

                  </button>

                </div>

              )}

            </div>

          </section>

        </div>

        {/* FOOTER */}

        <footer className="flex h-2 shrink-0 items-center justify-between pt-1 text-[10px] text-slate-400 mt-3">

          <span>NothiLipi.AI · Word to PDF</span>

          <span>Secure Document Workspace</span>

        </footer>

      </div>

      {/* --------------------------------------------------
          SHARE DOWNLOAD LINK MODAL
      -------------------------------------------------- */}

      {shareModalOpen && (

        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 py-6 backdrop-blur-[2px]"
          onClick={() => setShareModalOpen(false)}
        >

          <div
            className="relative w-full max-w-[500px] overflow-hidden rounded-xl bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >

            {/* CLOSE BUTTON */}

            <button
              type="button"
              onClick={() => setShareModalOpen(false)}
              title="Close"
              className="absolute right-4 top-4 z-10 rounded-full p-1 text-slate-600 transition hover:bg-slate-100 hover:text-black"
            >
              <X size={22} />
            </button>

            {/* MODAL CONTENT */}

            <div className="max-h-[85vh] overflow-y-auto px-5 py-8 sm:px-8">

              {/* TITLE */}

              <h2 className="mb-7 text-center text-lg font-semibold text-slate-800 sm:text-xl">
                Copy & Send download link
              </h2>

              {/* DOWNLOAD LINK AND COPY BUTTON */}

              <div className="mx-auto flex max-w-[360px] overflow-hidden rounded-md border border-slate-300">

                <div className="flex min-w-0 flex-1 items-center gap-2 px-3 py-3">

                  <ExternalLink
                    size={17}
                    className="shrink-0 text-slate-500"
                  />

                  <a
                    href={shareUrl}
                    className="truncate text-sm text-blue-600 hover:underline"
                    title={shareUrl}
                  >
                    {shareUrl}
                  </a>

                </div>

                <button
                  type="button"
                  onClick={handleCopyShareLink}
                  className="flex shrink-0 items-center gap-2 bg-red-500 px-4 text-xs font-bold text-white transition hover:bg-red-600"
                >

                  {copySuccess ? (
                    <CheckCircle size={15} />
                  ) : (
                    <Copy size={15} />
                  )}

                  {copySuccess ? "COPIED" : "COPY"}

                </button>

              </div>

              {/* QR CODE HEADING */}

              <h3 className="mt-10 text-center text-lg font-semibold text-slate-800">
                Instantly download to your phone
              </h3>

              {/* QR CODE */}

              <div className="mt-6 flex justify-center">

                <div className="rounded-lg bg-white p-3">

                  <QRCodeSVG
                    value={shareUrl}
                    size={250}
                    level="H"
                    includeMargin={true}
                    bgColor="#ffffff"
                    fgColor="#343a40"
                  />

                </div>

              </div>

              {/* DESCRIPTION */}

              <p className="mt-5 text-center text-xs leading-5 text-slate-500">
                Scan this QR code using your mobile camera
                to download the PDF directly to your device.
              </p>

              {/* FILE NAME */}

              <div className="mt-5 flex items-center justify-center gap-2 rounded-lg bg-slate-50 px-3 py-2">

                <FileType
                  size={16}
                  className="text-red-500"
                />

                <span className="max-w-[250px] truncate text-xs font-medium text-slate-600">
                  {convertedPdf?.name}
                </span>

              </div>

            </div>

          </div>

        </div>

      )}

    </main>
  );
}

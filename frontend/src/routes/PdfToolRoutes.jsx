
import { Navigate, Route, Routes } from "react-router-dom";

// Convert PDF
// import PdfToWord from "../pages/pdf-tools/convert/PdfToWord";
// import PdfToExcel from "../pages/pdf-tools/convert/PdfToExcel";
// import PdfToPowerPoint from "../pages/pdf-tools/convert/PdfToPowerPoint";
// import PdfToJpg from "../pages/pdf-tools/convert/PdfToJpg";
// import PdfToPdfA from "../pages/pdf-tools/convert/PdfToPdfA";
import WordToPdf from "../pages/pdf-tools/convert/WordToPdf";
// import ExcelToPdf from "../pages/pdf-tools/convert/ExcelToPdf";
// import PowerPointToPdf from "../pages/pdf-tools/convert/PowerPointToPdf";
// import JpgToPdf from "../pages/pdf-tools/convert/JpgToPdf";
// import HtmlToPdf from "../pages/pdf-tools/convert/HtmlToPdf";

export default function PdfToolRoutes() {
  return (
    <Routes>
      {/* Convert PDF */}
      {/* <Route path="pdf-to-word" element={<PdfToWord />} />
      <Route path="pdf-to-excel" element={<PdfToExcel />} />
      <Route path="pdf-to-powerpoint" element={<PdfToPowerPoint />} />
      <Route path="pdf-to-jpg" element={<PdfToJpg />} />
      <Route path="pdf-to-pdfa" element={<PdfToPdfA />} /> */}
      <Route path="word-to-pdf" element={<WordToPdf />} />
      {/* <Route path="excel-to-pdf" element={<ExcelToPdf />} />
      <Route path="powerpoint-to-pdf" element={<PowerPointToPdf />} />
      <Route path="jpg-to-pdf" element={<JpgToPdf />} />
      <Route path="html-to-pdf" element={<HtmlToPdf />} /> */}

      

      {/* Invalid PDF tool route */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

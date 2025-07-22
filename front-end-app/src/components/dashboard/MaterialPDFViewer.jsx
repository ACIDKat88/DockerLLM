// src/components/dashboard/MaterialPDFViewer.jsx
import React, { useState } from "react";
import { Container, Paper, IconButton, Typography } from "@mui/material";
import { ArrowBack, ArrowForward } from "@mui/icons-material";
import { Document, Page, pdfjs } from "react-pdf";

// Configure PDF.js worker for Vite
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.js",
  import.meta.url
).toString();

function MaterialPdfViewer({ pdfUrl }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);

  const handleLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  const goToPrevPage = () => setPageNumber((p) => Math.max(1, p - 1));
  const goToNextPage = () => setPageNumber((p) => Math.min(numPages, p + 1));

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 2, textAlign: "center" }}>
        <Document file={pdfUrl} onLoadSuccess={handleLoadSuccess}>
          <Page pageNumber={pageNumber} width={600} />
        </Document>
        <Typography sx={{ mt: 2 }}>
          Page {pageNumber} of {numPages}
        </Typography>
        <div>
          <IconButton onClick={goToPrevPage} disabled={pageNumber <= 1}>
            <ArrowBack />
          </IconButton>
          <IconButton onClick={goToNextPage} disabled={pageNumber >= numPages}>
            <ArrowForward />
          </IconButton>
        </div>
      </Paper>
    </Container>
  );
}

export default MaterialPdfViewer;

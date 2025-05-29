import React from 'react';
import { useParams } from 'react-router-dom';

function PDFViewer() {
  // In v6, using "*" will capture the rest of the URL (including subfolders)
  const { "*": pdfFilename } = useParams();
  // Build the URL to your FastAPI endpoint
  const pdfUrl = `http://localhost/api/pdf/${pdfFilename}`;

  return (
    <div style={{ height: '100vh' }}>
      <h2>PDF Viewer: {pdfFilename}</h2>
      <iframe
        src={pdfUrl}
        title="PDF Viewer"
        style={{ width: '100%', height: '90vh', border: 'none' }}
      ></iframe>
    </div>
  );
}

export default PDFViewer;

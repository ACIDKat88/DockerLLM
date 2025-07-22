import React from 'react';
import { useParams } from 'react-router-dom';

function PDFViewer() {
  const { pdfFilename } = useParams();
  const pdfUrl = `https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net/api/pdf/${pdfFilename}`;

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

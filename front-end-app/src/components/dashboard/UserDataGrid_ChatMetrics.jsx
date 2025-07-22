import * as React from 'react';
import { DataGrid } from '@mui/x-data-grid';
import Box from '@mui/material/Box';

/**
 * UserDataGrid_ChatMetrics
 * A DataGrid displaying chat interaction metrics.
 *
 * Columns:
 * - chat_id: Unique identifier for the chat.
 * - elapsed_time: Response time (in seconds).
 * - rouge1, rouge2, rougeL: ROUGE scores.
 * - bert_p, bert_r, bert_f1: BERT evaluation metrics.
 * - cosine_similarity: Cosine similarity between prediction and reference embeddings.
 *
 * @param {Array} rows - The data rows for the grid.
 */
export default function UserDataGrid_ChatMetrics({ rows = [] }) {
  const columns = [
    { field: 'office_id', headerName: 'Office', width: 150 },
    { field: 'elapsed_time', headerName: 'Response Time (s)', width: 150 },
    { field: 'pdf_file', headerName: 'PDF File', width: 250 },
    { field: 'average_cosine', headerName: 'Avg Cosine Similarity', width: 200, type: 'number' },
 
  ];

  return (
    <Box>
      <DataGrid
        rows={rows}
        columns={columns}
        getRowId={(row) => row.chat_id} // Ensure each row has a unique chat_id
        checkboxSelection
        initialState={{
          pagination: { paginationModel: { pageSize: 20 } },
        }}
        pageSizeOptions={[10, 20, 50]}
        disableColumnResize
        density="compact"
      />
    </Box>
  );
}


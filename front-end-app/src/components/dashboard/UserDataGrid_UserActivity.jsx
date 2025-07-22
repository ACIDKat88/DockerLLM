import * as React from 'react';
import { DataGrid } from '@mui/x-data-grid';
import Box from '@mui/material/Box';

/**
 * UserDataGrid_ChatMetricsModified
 * A DataGrid displaying selected chat feedback metrics.
 *
 * Columns:
 * - user_id: The ID of the user.
 * - office_id: The ID of the office.
 * - question: The feedback question.
 * - pdf_file: The name of the PDF file.
 * - cosine_similarity: The cosine similarity score.
 *
 * @param {Array} rows - The data rows for the grid.
 */
export default function UserDataGrid_UserActivity({ rows = [] }) {
  const columns = [
    { field: 'user_id', headerName: 'User ID', width: 150 },
    { field: 'office_id', headerName: 'Office ID', width: 150 },
    { field: 'question', headerName: 'Question', width: 300 },
    { field: 'pdf_file', headerName: 'PDF File', width: 200 },
    { field: 'cosine_similarity', headerName: 'Cosine Similarity', width: 150 },
  ];

  return (
    <Box>
      <DataGrid
        rows={rows}
        columns={columns}
        getRowId={(row) => `${row.user_id}-${row.office_id}-${row.question}`} // Unique row ID
        initialState={{
          pagination: { paginationModel: { pageSize: 20 } },
        }}
        pageSizeOptions={[10, 20, 50]}
        density="compact"
      />
    </Box>
  );
}

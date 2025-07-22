import * as React from 'react';
import { DataGrid } from '@mui/x-data-grid';
import Box from '@mui/material/Box';

export default function CustomizedDataGrid_OfficeMabStats({ rows = [] }) {
  // Updated columns to match the aggregated data (grouped only by url_id)
  const columns = [
    { field: 'url_id', headerName: 'URL ID', width: 80 },
    { field: 'total_clicks', headerName: 'Clicks', width: 80 },
    { field: 'total_impressions', headerName: 'Impressions', width: 110 },
    { field: 'office_ctr', headerName: 'CTR', width: 80 },
    { field: 'total_bookmarks', headerName: 'Bookmarks', width: 110 },
    { field: 'total_adds', headerName: 'Adds', width: 80 },
  ];

  // Use url_id as the unique row key
  function getRowId(row) {
    return row.url_id;
  }

  return (
    <Box sx={{ width: '100%', height: '100%' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        getRowId={getRowId}
        checkboxSelection
        disableColumnResize
        density="compact"
        pageSizeOptions={[10, 20, 50]}
        initialState={{
          pagination: { paginationModel: { pageSize: 10 } },
        }}
      />
    </Box>
  );
}

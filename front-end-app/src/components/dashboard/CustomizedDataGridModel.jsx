import * as React from 'react';
import { DataGrid } from '@mui/x-data-grid';
import Box from '@mui/material/Box';

export default function CustomizedDataGrid({ rows = [] }) {
  const columns = [
    { field: 'mab_rank_log_id', headerName: 'Log ID', width: 90 },
    { field: 'created_at', headerName: 'Created At', width: 160 },
    { field: 'office_id', headerName: 'Office ID', width: 220 },
    { field: 'user_id', headerName: 'User ID', width: 220 },
    { field: 'session_id', headerName: 'Session ID', width: 220 },
    { field: 'url_id', headerName: 'URL ID', width: 70 },
    { field: 'rank_position', headerName: 'Rank', width: 70 },
    { field: 'impressions_count', headerName: 'Impr.', width: 80 },
    { field: 'clicks_count', headerName: 'Clicks', width: 80 },
    { field: 'ucb_value', headerName: 'UCB', width: 80 },
    { field: 'time_index_t', headerName: 'Time Index', width: 100 },
    { field: 'c_param', headerName: 'C Param', width: 80 },
    { field: 'cold_threshold', headerName: 'Cold Thr.', width: 100 },
    {
      field: 'filter_topics',
      headerName: 'Filter Topics',
      width: 180,
      // If you'd like to display the array as a comma-separated string:
      // valueGetter: (params) => params.value?.join(", "),
    },
    { field: 'filter_date', headerName: 'Filter Date', width: 120 },
  ];

  return (
    <DataGrid
      rows={rows}
      columns={columns}
      getRowId={(row) => row.mab_rank_log_id}
      checkboxSelection
      getRowClassName={(params) =>
        params.indexRelativeToCurrentPage % 2 === 0 ? 'even' : 'odd'
      }
      initialState={{
        pagination: { paginationModel: { pageSize: 20 } },
      }}
      pageSizeOptions={[10, 20, 50]}
      disableColumnResize
      density="compact"
      slotProps={{
        filterPanel: {
          filterFormProps: {
            logicOperatorInputProps: {
              variant: 'outlined',
              size: 'small',
            },
            columnInputProps: {
              variant: 'outlined',
              size: 'small',
              sx: { mt: 'auto' },
            },
            operatorInputProps: {
              variant: 'outlined',
              size: 'small',
              sx: { mt: 'auto' },
            },
            valueInputProps: {
              InputComponentProps: {
                variant: 'outlined',
                size: 'small',
              },
            },
          },
        },
      }}
    />
  );
}

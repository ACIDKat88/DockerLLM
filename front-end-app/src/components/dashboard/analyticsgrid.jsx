import React, { useState, useEffect } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import { Box, Typography } from '@mui/material';
import axios from 'axios';
export const BASE_URL = "https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net";

const AnalyticsGrid = () => {
  const [analyticsData, setAnalyticsData] = useState([]);
  const token = localStorage.getItem("session_token") || "";
  const headers = { Authorization: token };

  const fetchAnalytics = () => {
    axios
      .get(`${BASE_URL}/api/analytics?cb=${new Date().getTime()}`, { headers })
      .then((response) => {
        console.log("Analytics data:", response.data);
        // Check if any records have RAGAS metrics
        if (response.data.length > 0) {
          console.log("First record:", response.data[0]);
          console.log("RAGAS metrics in first record:", {
            faithfulness: response.data[0].faithfulness,
            answer_relevancy: response.data[0].answer_relevancy,
            context_relevancy: response.data[0].context_relevancy,
            context_precision: response.data[0].context_precision,
            context_recall: response.data[0].context_recall,
            harmfulness: response.data[0].harmfulness
          });
          
          // Count records with each RAGAS metric
          const metrics = {
            faithfulness: response.data.filter(item => item.faithfulness !== null && item.faithfulness !== undefined).length,
            answer_relevancy: response.data.filter(item => item.answer_relevancy !== null && item.answer_relevancy !== undefined).length,
            context_relevancy: response.data.filter(item => item.context_relevancy !== null && item.context_relevancy !== undefined).length,
            context_precision: response.data.filter(item => item.context_precision !== null && item.context_precision !== undefined).length,
            context_recall: response.data.filter(item => item.context_recall !== null && item.context_recall !== undefined).length,
            harmfulness: response.data.filter(item => item.harmfulness !== null && item.harmfulness !== undefined).length
          };
          console.log("Records with RAGAS metrics:", metrics);
        }
        setAnalyticsData(response.data);
      })
      .catch((error) => console.error("Error fetching analytics:", error));
  };

  useEffect(() => {
    fetchAnalytics(); // Initial fetch
    const intervalId = setInterval(fetchAnalytics, 10000); // Poll every 10 seconds
    return () => clearInterval(intervalId);
  }, [token]);

  // RAGAS metrics renderCell function with indicator for metric presence
  const renderRagasMetricCell = (params, metricName) => {
    if (!params || params.value === null || params.value === undefined) return <div style={{ textAlign: 'center', width: '100%' }}>N/A</div>;
    
    // Format as percentage and add an indicator for metric presence
    return (
      <div style={{ 
        textAlign: 'center', 
        width: '100%', 
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: params.value > 0.7 ? 'green' : params.value < 0.3 ? 'red' : 'inherit',
        fontWeight: 'bold' // Make bold to emphasize these are RAGAS metrics
      }}>
        {`${Math.round(params.value * 100)}%`} ✓
      </div>
    );
  };

  const columns = [
    { field: 'username', headerName: 'Username', flex: 1, minWidth: 120, headerAlign: 'center' },
    { field: 'office_code', headerName: 'Office Code', flex: 1, minWidth: 120, headerAlign: 'center' },
    { field: 'model', headerName: 'Model', flex: 1, minWidth: 120, headerAlign: 'center', align: 'center',
      renderCell: (params) => (
        <div style={{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.2em', textAlign: 'center', width: '100%' }}>
          {params.value || ''}
        </div>
      )
    },
    { 
      field: 'question', 
      headerName: 'Question', 
      flex: 2.5, 
      minWidth: 200,
      headerAlign: 'center',
      renderCell: (params) => (
        <div style={{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.2em' }}>
          {params.value}
        </div>
      ),
    },
    {
      field: 'answer',
      headerName: 'Answer',
      flex: 3,
      minWidth: 250,
      headerAlign: 'center',
      renderCell: (params) => (
        <div style={{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.2em' }}>
          {params.value}
        </div>
      ),
    },
    { 
      field: 'feedback', 
      headerName: 'Feedback', 
      flex: 0.8, 
      minWidth: 100,
      headerAlign: 'center',
      align: 'center',
      renderCell: (params) => {
        const value = params.value;
        if (typeof value === 'string') {
          const lowerCaseValue = value.toLowerCase();
          if (lowerCaseValue === 'positive') {
            return <div style={{ textAlign: 'center', width: '100%' }}>Positive</div>;
          } else if (lowerCaseValue === 'negative') {
            return <div style={{ textAlign: 'center', width: '100%' }}>Negative</div>;
          } else if (lowerCaseValue === 'neutral') {
            return <div style={{ textAlign: 'center', width: '100%' }}>Neutral</div>;
          }
        }
        // Return original value if it's not a recognized string or not a string at all
        return <div style={{ textAlign: 'center', width: '100%' }}>{value}</div>; 
      }
    },
    { 
      field: 'sources', 
      headerName: 'Sources', 
      flex: 1.5, 
      minWidth: 120,
      headerAlign: 'center',
      renderCell: (params) => (
        <div style={{ whiteSpace: 'normal', wordBreak: 'break-word', lineHeight: '1.2em' }}>
          {params.value}
        </div>
      ),
    },
    { 
      field: 'node_count', 
      headerName: 'Retrieved Nodes', 
      flex: 1.2, 
      minWidth: 150,
      headerAlign: 'center',
      align: 'center',
      renderCell: (params) => (
        <div style={{ 
          textAlign: 'center', 
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%'
        }}>
          {params.value}
        </div>
      ),
    },
    { 
      field: 'cosine_similarity', 
      headerName: 'Accuracy', 
      flex: 0.7, 
      minWidth: 100, 
      type: 'number',
      headerAlign: 'center',
      align: 'center',
      valueFormatter: (params) => {
        if (!params || params.value === null || params.value === undefined) return 'N/A';
        return `${Math.round(params.value * 100)}%`;
      },
      renderCell: (params) => {
        if (!params || params.value === null || params.value === undefined) return <div style={{ textAlign: 'center', width: '100%' }}>N/A</div>;
        return (
          <div style={{ textAlign: 'center', width: '100%' }}>
            {`${Math.round(params.value * 100)}%`}
          </div>
        );
      }
    },
    { 
      field: 'response_time', 
      headerName: 'Response Time (s)', 
      flex: 0.8, 
      minWidth: 150,
      type: 'number',
      headerAlign: 'center',
      align: 'center',
      valueFormatter: (params) => {
        // Add more debugging to see what's coming in
        console.log("Response time value:", params?.value, typeof params?.value);
        if (!params || params.value === null || params.value === undefined) return 'N/A';
        return Number(params.value).toFixed(1);
      },
      // Add renderCell to ensure we're displaying the value correctly
      renderCell: (params) => {
        if (!params || params.value === null || params.value === undefined) return <div style={{ textAlign: 'center', width: '100%' }}>N/A</div>;
        return (
          <div style={{ textAlign: 'center', width: '100%' }}>
            {Number(params.value).toFixed(1)}
          </div>
        );
      }
    },
    { 
      field: 'timestamp', 
      headerName: 'Timestamp', 
      flex: 1.2, 
      minWidth: 150,
      headerAlign: 'center',
      align: 'center'
    },
    // RAGAS metrics columns
    { 
      field: 'faithfulness', 
      headerName: 'Faithfulness', 
      flex: 0.8, 
      minWidth: 120,
      type: 'number',
      headerAlign: 'center',
      align: 'center',
      valueFormatter: (params) => {
        if (!params || params.value === null || params.value === undefined) return 'N/A';
        return `${Math.round(params.value * 100)}%`;
      },
      renderCell: (params) => renderRagasMetricCell(params, 'faithfulness')
    },
    { 
      field: 'answer_relevancy', 
      headerName: 'Answer Relevancy', 
      flex: 0.8, 
      minWidth: 140,
      type: 'number',
      headerAlign: 'center',
      align: 'center',
      valueFormatter: (params) => {
        if (!params || params.value === null || params.value === undefined) return 'N/A';
        return `${Math.round(params.value * 100)}%`;
      },
      renderCell: (params) => renderRagasMetricCell(params, 'answer_relevancy')
    },
    { 
      field: 'context_relevancy', 
      headerName: 'Context Relevancy', 
      flex: 0.8, 
      minWidth: 140,
      type: 'number',
      headerAlign: 'center',
      align: 'center',
      valueFormatter: (params) => {
        if (!params || params.value === null || params.value === undefined) return 'N/A';
        return `${Math.round(params.value * 100)}%`;
      },
      renderCell: (params) => renderRagasMetricCell(params, 'context_relevancy')
    },
    { 
      field: 'context_precision', 
      headerName: 'Context Precision', 
      flex: 0.8, 
      minWidth: 140,
      type: 'number',
      headerAlign: 'center',
      align: 'center',
      valueFormatter: (params) => {
        if (!params || params.value === null || params.value === undefined) return 'N/A';
        return `${Math.round(params.value * 100)}%`;
      },
      renderCell: (params) => renderRagasMetricCell(params, 'context_precision')
    },
    { 
      field: 'context_recall', 
      headerName: 'Context Recall', 
      flex: 0.8, 
      minWidth: 130,
      type: 'number',
      headerAlign: 'center',
      align: 'center',
      valueFormatter: (params) => {
        if (!params || params.value === null || params.value === undefined) return 'N/A';
        return `${Math.round(params.value * 100)}%`;
      },
      renderCell: (params) => renderRagasMetricCell(params, 'context_recall')
    },
    { 
      field: 'harmfulness', 
      headerName: 'Harmfulness', 
      flex: 0.8, 
      minWidth: 120,
      type: 'number',
      headerAlign: 'center',
      align: 'center',
      valueFormatter: (params) => {
        if (!params || params.value === null || params.value === undefined) return 'N/A';
        return `${Math.round(params.value * 100)}%`;
      },
      renderCell: (params) => {
        if (!params || params.value === null || params.value === undefined) return <div style={{ textAlign: 'center', width: '100%' }}>N/A</div>;
        return (
          <div style={{ textAlign: 'center', width: '100%', color: params.value > 0.3 ? 'red' : 'green', fontWeight: 'bold' }}>
            {`${Math.round(params.value * 100)}%`} ✓
          </div>
        );
      }
    },
  ];
  
  return (
    <Box sx={{ width: '100%', mt: 2 }}>
      <DataGrid
        rows={analyticsData}
        columns={columns}
        getRowId={(row) => row.timestamp + row.username} // Combining fields for uniqueness
        pageSizeOptions={[10, 20, 50]}
        initialState={{
          pagination: { paginationModel: { pageSize: 10 } },
        }}
        autoHeight
        sx={{ 
            // Optional: Add styling for better appearance if needed
            // e.g., border: '1px solid #ccc' 
        }}
      />
    </Box>
  );
};

export default AnalyticsGrid;

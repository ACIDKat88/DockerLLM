import React, { useState, useEffect } from 'react';
import { Grid, Typography, Box } from '@mui/material';
import { fetchChatMetrics } from '../../api.js';
import UserDataGrid_UsersList from './UserDataGrid_ChatMetrics';

export default function UserAnalytics() {
  const [chatMetrics, setChatMetrics] = useState([]);
  const sessionToken = localStorage.getItem("session_token") || "";

  useEffect(() => {
    fetchChatMetrics(sessionToken)
      .then(response => {
        // Assume response.metrics is an array of objects with pdf_file and cosine_similarity
        const data = response.metrics || [];
        setChatMetrics(data);
      })
      .catch(error => {
        console.error("Error fetching chat metrics:", error);
      });
  }, [sessionToken]);

  // Aggregate metrics: group by pdf_file and compute the average cosine similarity.
  const aggregated = chatMetrics.reduce((acc, curr) => {
    const file = curr.pdf_file || 'unknown';
    if (!acc[file]) {
      acc[file] = { total: 0, count: 0 };
    }
    acc[file].total += curr.cosine_similarity;
    acc[file].count += 1;
    return acc;
  }, {});

  const averageMetrics = Object.keys(aggregated).map(file => ({
    pdf_file: file,
    average_cosine: aggregated[file].total / aggregated[file].count,
  }));

  return (
    <Grid container spacing={3} sx={{ mt: 4 }}>
      <Grid item xs={12}>
        <Typography variant="h6" sx={{ textAlign: 'center', mb: 2 }}>
          Average Cosine Similarity by PDF File
        </Typography>
        <Box sx={{ mx: 'auto', width: '80%' }}>
          <UserDataGrid_AvgCosine rows={averageMetrics} />
        </Box>
      </Grid>
    </Grid>
  );
}

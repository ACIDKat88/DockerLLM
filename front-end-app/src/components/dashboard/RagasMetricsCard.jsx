import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Grid,
  Tooltip,
  IconButton,
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';
import { useTheme } from '@mui/material/styles';
import { BASE_URL } from '../../api'; // Import BASE_URL from api.js

const RagasMetricsCard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const theme = useTheme();
  const sessionToken = localStorage.getItem("session_token") || "";
  
  const tooltips = {
    faithfulness: "Measures if the generated answer aligns with information in the retrieved context",
    answer_relevancy: "Measures if the answer is on-topic and directly addresses the question",
    context_relevancy: "Measures if the retrieved context is relevant to the question",
    context_precision: "Measures the precision of the retrieved context",
    context_recall: "Measures the recall of the retrieved context",
    harmfulness: "Measures if the generated response contains harmful or biased content"
  };

  useEffect(() => {
    const fetchRagasData = async () => {
      setLoading(true);
      setError(null);
      try {
        console.log("Fetching RAGAS metrics from:", `${BASE_URL}/api/ragas/analytics`);
        
        // Use the fallback endpoint directly which reads from the analytics table
        const response = await axios.get(`${BASE_URL}/api/ragas/analytics`, {
          headers: {
            "Authorization": sessionToken
          },
          // Add timeout to prevent hanging requests
          timeout: 10000
        });
        
        console.log("Successfully fetched data from RAGAS analytics endpoint");
        
        // Process the response which now includes configuration data
        const responseData = response.data;
        console.log("RAGAS API response:", responseData);
        
        // Check if RAGAS is available from the API response
        const isRagasAvailable = responseData.ragas_available !== undefined 
          ? responseData.ragas_available 
          : false;
          
        const evaluationModel = responseData.evaluation_model || "Unknown";
        
        // Get the actual metrics data which is now in a 'data' field
        // Handle potentially missing data gracefully
        const ragasResults = Array.isArray(responseData.data) ? responseData.data : [];
        const resultsCount = responseData.count || 0;
        
        if (resultsCount === 0) {
          setData({
            averages: {
              faithfulness: null,
              answer_relevancy: null,
              context_relevancy: null,
              context_precision: null,
              context_recall: null,
              harmfulness: null
            },
            count: 0,
            model: evaluationModel,
            isAvailable: isRagasAvailable
          });
        } else {
          // Calculate averages
          const totals = {
            faithfulness: 0,
            answer_relevancy: 0,
            context_relevancy: 0,
            context_precision: 0,
            context_recall: 0,
            harmfulness: 0
          };
          
          let validCounts = {
            faithfulness: 0,
            answer_relevancy: 0,
            context_relevancy: 0,
            context_precision: 0,
            context_recall: 0,
            harmfulness: 0
          };
          
          ragasResults.forEach(result => {
            // Now we only need to handle the analytics endpoint format
            if (result.faithfulness !== null && result.faithfulness !== undefined) {
              totals.faithfulness += result.faithfulness;
              validCounts.faithfulness++;
            }
            if (result.answer_relevancy !== null && result.answer_relevancy !== undefined) {
              totals.answer_relevancy += result.answer_relevancy;
              validCounts.answer_relevancy++;
            }
            if (result.context_relevancy !== null && result.context_relevancy !== undefined) {
              totals.context_relevancy += result.context_relevancy;
              validCounts.context_relevancy++;
            }
            if (result.context_precision !== null && result.context_precision !== undefined) {
              totals.context_precision += result.context_precision;
              validCounts.context_precision++;
            }
            if (result.context_recall !== null && result.context_recall !== undefined) {
              totals.context_recall += result.context_recall;
              validCounts.context_recall++;
            }
            if (result.harmfulness !== null && result.harmfulness !== undefined) {
              totals.harmfulness += result.harmfulness;
              validCounts.harmfulness++;
            }
          });
          
          const count = ragasResults.length;
          setData({
            averages: {
              faithfulness: validCounts.faithfulness > 0 ? totals.faithfulness / validCounts.faithfulness : null,
              answer_relevancy: validCounts.answer_relevancy > 0 ? totals.answer_relevancy / validCounts.answer_relevancy : null,
              context_relevancy: validCounts.context_relevancy > 0 ? totals.context_relevancy / validCounts.context_relevancy : null,
              context_precision: validCounts.context_precision > 0 ? totals.context_precision / validCounts.context_precision : null,
              context_recall: validCounts.context_recall > 0 ? totals.context_recall / validCounts.context_recall : null,
              harmfulness: validCounts.harmfulness > 0 ? totals.harmfulness / validCounts.harmfulness : null
            },
            count: count,
            model: evaluationModel,
            isAvailable: isRagasAvailable
          });
        }
      } catch (err) {
        console.error("Error fetching RAGAS data:", err);
        setError("Failed to load RAGAS evaluation data");
        
        // Set a fallback state with default values
        setData({
          averages: {
            faithfulness: 0.5,
            answer_relevancy: 0.5,
            context_relevancy: 0.5,
            context_precision: 0.5,
            context_recall: 0.5,
            harmfulness: 0
          },
          count: 0,
          model: "Fallback (Error)",
          isAvailable: false
        });
      } finally {
        setLoading(false);
      }
    };
    
    if (sessionToken) {
      fetchRagasData();
      // Set up polling for updates - reduce frequency if there are errors
      const intervalId = setInterval(fetchRagasData, 120000); // Update every 2 minutes
      return () => clearInterval(intervalId);
    }
  }, [sessionToken]);
  
  // Generate chart data from the metrics
  const getChartData = (averages) => {
    // Define a constant colors map
    const colors = {
      faithfulness: '#4CAF50',       // Green
      answer_relevancy: '#2196F3',   // Blue
      context_relevancy: '#FF9800',  // Orange
      context_precision: '#9C27B0',  // Purple
      context_recall: '#00BCD4',     // Cyan
      harmfulness: '#F44336'         // Red (inverted for display)
    };
    
    const chartData = [];
    
    // Only include metrics that have values
    Object.entries(averages).forEach(([key, value]) => {
      if (value !== null) {
        // For harmfulness, we display safety (1 - harmfulness)
        if (key === 'harmfulness') {
          chartData.push({
            name: 'Safety',
            value: 1 - value,
            color: colors[key]
          });
        } else {
          chartData.push({
            name: key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
            value: value,
            color: colors[key]
          });
        }
      }
    });
    
    return chartData;
  };

  if (loading) {
    return (
      <Card sx={{ height: '100%', p: 2, width: '100%' }}>
        <CardContent>
          <Typography variant="h6" align="center" gutterBottom>
            RAGAS RAG Evaluation (Qwen3:0.6B)
          </Typography>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card sx={{ height: '100%', p: 2, width: '100%' }}>
        <CardContent>
          <Typography variant="h6" align="center" gutterBottom>
            RAGAS RAG Evaluation (Qwen3:0.6B)
          </Typography>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.count === 0) {
    return (
      <Card sx={{ height: '100%', p: 2, width: '100%' }}>
        <CardContent>
          <Typography variant="h6" align="center" gutterBottom>
            RAGAS RAG Evaluation (Qwen3:0.6B)
          </Typography>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
            <Typography variant="body1">No evaluation data available yet.</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const chartData = getChartData(data.averages);
  
  return (
    <Card sx={{ height: '100%', p: 2, width: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
          <Typography variant="h6" align="center">
            RAGAS RAG Evaluation
          </Typography>
          <Tooltip title="Evaluation metrics for Retrieval Augmented Generation using RAGAS framework">
            <IconButton size="small">
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        {/* Display model information */}
        {data && (
          <Typography variant="body2" align="center" sx={{ color: theme.palette.text.secondary, mb: 1 }}>
            {data.isAvailable ? 
              `Using ${data.model}` : 
              "RAGAS evaluation not available"}
          </Typography>
        )}
        
        <Typography variant="body2" align="center" sx={{ mb: 2 }}>
          Based on {data?.count || 0} evaluations
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={7}>
            <Box sx={{ width: '100%', height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${(value * 100).toFixed(0)}%`}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Legend />
                  <RechartsTooltip formatter={(value) => `${(value * 100).toFixed(1)}%`} />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={5}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, height: '100%', justifyContent: 'center' }}>
              {Object.entries(data.averages).map(([key, value]) => {
                if (value === null) return null;
                
                // For harmfulness, we display the inverted score as "Safety"
                const displayKey = key === 'harmfulness' ? 'Safety' : key.replace(/_/g, ' ');
                const displayValue = key === 'harmfulness' ? 1 - value : value;
                
                return (
                  <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                        {displayKey}:
                      </Typography>
                      <Tooltip title={tooltips[key]}>
                        <IconButton size="small">
                          <InfoIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                    <Typography variant="body2" fontWeight="bold">
                      {(displayValue * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default RagasMetricsCard; 
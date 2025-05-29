import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTheme } from '@mui/material/styles';

const DatasetCosineChart = ({ analyticsData = [] }) => {
  const theme = useTheme();
  const chartTextColor = theme.palette.text.primary;
  const chartGridColor = theme.palette.divider;
  const chartTooltipBg = theme.palette.background.paper;
  const barColor = theme.palette.secondary.main;

  // Process data to calculate average cosine score by dataset
  const processData = () => {
    if (!Array.isArray(analyticsData) || analyticsData.length === 0) return [];
    
    const datasetScores = {};
    const datasetCounts = {};
    
    analyticsData.forEach(item => {
      if (item.dataset && item.cosine_similarity !== null && item.cosine_similarity !== undefined) {
        const dataset = item.dataset;
        if (!datasetScores[dataset]) {
          datasetScores[dataset] = 0;
          datasetCounts[dataset] = 0;
        }
        datasetScores[dataset] += parseFloat(item.cosine_similarity);
        datasetCounts[dataset]++;
      }
    });
    
    return Object.keys(datasetScores).map(dataset => ({
      dataset,
      averageScore: Math.round(datasetScores[dataset] / datasetCounts[dataset] * 100) // Convert to percentage and round
    })).sort((a, b) => b.averageScore - a.averageScore); // Sort by score descending
  };

  const chartData = processData();

  // Custom tooltip formatter to display percentages
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Box
          sx={{
            backgroundColor: chartTooltipBg,
            padding: '10px',
            border: `1px solid ${chartGridColor}`,
            borderRadius: 1
          }}
        >
          <Typography variant="body2" color={chartTextColor}>
            <strong>{label}</strong>
          </Typography>
          <Typography variant="body2" color={chartTextColor}>
            Average Accuracy: {payload[0].value}%
          </Typography>
        </Box>
      );
    }
    return null;
  };

  return (
    <Card sx={{ height: '100%', p: 2 }}>
      <CardContent>
        <Typography variant="h6" align="center" gutterBottom>
          Average Accuracy by Dataset
        </Typography>
        
        {chartData.length === 0 ? (
          <Typography variant="body1" align="center" sx={{ mt: 4 }}>
            No accuracy data available.
          </Typography>
        ) : (
          <Box sx={{ width: '100%', height: 300, mt: 2 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 5, right: 30, left: 20, bottom: 25 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} />
                <XAxis 
                  dataKey="dataset" 
                  stroke={chartTextColor}
                  tick={(props) => {
                    const { x, y, payload } = props;
                    // Split the dataset name into lines if too long
                    const datasetName = payload.value;
                    const maxLineLength = 15; // Characters per line
                    let lines = [];
                    
                    if (datasetName.length <= maxLineLength) {
                      lines = [datasetName];
                    } else {
                      // Simple word wrap - split into chunks of maxLineLength
                      for (let i = 0; i < datasetName.length; i += maxLineLength) {
                        lines.push(datasetName.substring(i, i + maxLineLength));
                      }
                    }
                    
                    return (
                      <g transform={`translate(${x},${y})`}>
                        {lines.map((line, index) => (
                          <text
                            key={index}
                            x={0}
                            y={index * 12} // 12px line height
                            dy={16} // Offset from top
                            textAnchor="middle"
                            fill={chartTextColor}
                            fontSize={10}
                          >
                            {line}
                          </text>
                        ))}
                      </g>
                    );
                  }}
                  height={100} // Increased height to accommodate wrapped text
                />
                <YAxis 
                  stroke={chartTextColor} 
                  tick={{ fill: chartTextColor }}
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ color: chartTextColor }} />
                <Bar 
                  dataKey="averageScore" 
                  name="Average Accuracy (%)" 
                  fill={barColor} 
                  label={{ 
                    position: 'top',
                    formatter: (value) => `${value}%`,
                    fill: chartTextColor,
                    fontSize: 12
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default DatasetCosineChart; 
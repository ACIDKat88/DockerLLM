import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Box, Typography, Card, CardContent, useTheme } from '@mui/material';

const ModelAccuracyChart = ({ analyticsData }) => {
  const theme = useTheme();
  const chartTextColor = theme.palette.text.primary;
  const chartGridColor = theme.palette.divider;
  const chartTooltipBg = theme.palette.background.paper;
  const barColor = theme.palette.primary.main;

  // Process analytics data to calculate average accuracy by model
  const chartData = useMemo(() => {
    if (!Array.isArray(analyticsData) || analyticsData.length === 0) {
      return [];
    }

    // Group by model and calculate average cosine similarity
    const modelGroups = {};
    
    analyticsData.forEach(record => {
      if (!record.model || record.cosine_similarity === null || record.cosine_similarity === undefined) {
        return; // Skip records without model or cosine similarity data
      }
      
      const model = record.model.trim();
      if (!model) return; // Skip empty model names
      
      if (!modelGroups[model]) {
        modelGroups[model] = {
          totalSimilarity: 0,
          count: 0
        };
      }
      
      modelGroups[model].totalSimilarity += parseFloat(record.cosine_similarity);
      modelGroups[model].count += 1;
    });
    
    // Convert to chart format with percentage calculation
    return Object.keys(modelGroups).map(model => {
      const group = modelGroups[model];
      const averageSimilarity = group.count > 0 ? group.totalSimilarity / group.count : 0;
      return {
        model: model,
        averageAccuracy: Math.round(averageSimilarity * 100) // Convert to percentage
      };
    }).sort((a, b) => b.averageAccuracy - a.averageAccuracy); // Sort by accuracy descending
  }, [analyticsData]);

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
          Average Accuracy by Model
        </Typography>
        
        {chartData.length === 0 ? (
          <Typography variant="body1" align="center" sx={{ mt: 4 }}>
            No model accuracy data available.
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
                  dataKey="model" 
                  stroke={chartTextColor}
                  tick={(props) => {
                    const { x, y, payload } = props;
                    // Split the model name into lines if too long
                    const modelName = payload.value;
                    const maxLineLength = 15; // Characters per line
                    let lines = [];
                    
                    if (modelName.length <= maxLineLength) {
                      lines = [modelName];
                    } else {
                      // Simple word wrap - split into chunks of maxLineLength
                      for (let i = 0; i < modelName.length; i += maxLineLength) {
                        lines.push(modelName.substring(i, i + maxLineLength));
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
                  dataKey="averageAccuracy" 
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

export default ModelAccuracyChart; 
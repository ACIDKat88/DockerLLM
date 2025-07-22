import React from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Alert, CircularProgress } from '@mui/material';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTheme } from '@mui/material/styles';

export const BASE_URL = "https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net";

const OfficeQuestionsBarChart = ({ chartData = [] }) => {
  const theme = useTheme();
  const textColor = theme.palette.text.primary;
  const gridColor = theme.palette.divider;
  const tooltipBg = theme.palette.background.paper;

  const data = Array.isArray(chartData) ? chartData : [];

  return (
    <Card sx={{ height: '100%', p: 2 }}>
      <CardContent>
        <Typography variant="h6" align="center" gutterBottom>
          Questions Count by Office
        </Typography>
        
        {data.length === 0 ? (
          <Typography variant="body1" align="center" sx={{ mt: 4 }}>
            No data available.
          </Typography>
        ) : (
          <Box sx={{ width: '100%', height: 300, mt: 2 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="office_id" stroke={textColor} tick={{ fill: textColor }} />
                <YAxis allowDecimals={false} stroke={textColor} tick={{ fill: textColor }} />
                <Tooltip
                  contentStyle={{ backgroundColor: tooltipBg, border: `1px solid ${gridColor}` }}
                  labelStyle={{ color: textColor }}
                  itemStyle={{ color: textColor }}
                />
                <Legend wrapperStyle={{ color: textColor }} />
                <Bar dataKey="count" fill={theme.palette.primary.main} name="Questions Count" />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default OfficeQuestionsBarChart;

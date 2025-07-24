import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';

const AverageCosineCard = ({ analyticsData = [] }) => {
  // Calculate average cosine similarity from analytics data
  const calculateAverageAccuracy = () => {
    if (!Array.isArray(analyticsData) || analyticsData.length === 0) {
      return 'N/A';
    }

    let totalCosine = 0;
    let count = 0;

    analyticsData.forEach(record => {
      if (typeof record.cosine_similarity === 'number' && !isNaN(record.cosine_similarity)) {
        totalCosine += record.cosine_similarity;
        count++;
      }
    });

    if (count === 0) return 'N/A';
    
    // Convert to percentage and round to nearest integer
    return `${Math.round((totalCosine / count) * 100)}%`;
  };

  return (
    <Card sx={{ 
      height: '100%',
      p: 2
    }}>
      <CardContent>
        <Typography variant="h6" align="center" gutterBottom>
          Average Accuracy
        </Typography>
        <Typography variant="h4" component="div" align="center" sx={{ mt: 2 }}>
          {calculateAverageAccuracy()}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default AverageCosineCard; 

import React from 'react';
import { Box, Button, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const MenuContent = () => {
  const navigate = useNavigate();
  
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      <Typography variant="h6" component="div">
        J1 Dashboard
      </Typography>
      <Button onClick={() => navigate('/')} color="inherit">
        Home
      </Button>
    </Box>
  );
};

export default MenuContent; 
import React from 'react';
import Button from '@mui/material/Button';
import axios from 'axios';

function TestScriptButton() {
  const handleRunTestScript = async () => {
    try {
      const response = await axios.post('/api/run_test_script');
      console.log("Test script output:", response.data.output);
      alert("Test script executed successfully!");
    } catch (error) {
      console.error("Error running test script:", error);
      alert("Test script execution failed.");
    }
  };

  return (
    <Button
      variant="contained"
      color="secondary"
      onClick={handleRunTestScript}
      sx={{ position: 'absolute', bottom: 16, left: 16 }}
    >
      Run Test Script
    </Button>
  );
}

export default TestScriptButton;

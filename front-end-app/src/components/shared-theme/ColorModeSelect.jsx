import * as React from 'react';
import { useColorScheme } from '@mui/material/styles';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';

export default function ColorModeSelect(props) {
  const { mode, setMode } = useColorScheme();
  
  // Set mode to dark if it's currently light
  React.useEffect(() => {
    if (mode === 'light') {
      setMode('dark');
    }
  }, [mode, setMode]);
  
  if (!mode) {
    return null;
  }
  
  return (
    <Select
      value={mode === 'light' ? 'dark' : mode}
      onChange={(event) => setMode(event.target.value)}
      SelectDisplayProps={{
        'data-screenshot': 'toggle-mode',
      }}
      {...props}
    >
      <MenuItem value="system">System</MenuItem>
      <MenuItem value="dark">Dark</MenuItem>
    </Select>
  );
}

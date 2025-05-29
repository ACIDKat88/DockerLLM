import * as React from 'react';
import { alpha } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import MainGrid from '../components/dashboard/MainGrid.jsx';
import AppTheme from '../components/shared-theme/AppTheme.jsx';
import AppAppBar from '../components/shared-theme/AppAppBar.jsx';
import Toolbar from '@mui/material/Toolbar';  // Import Toolbar to serve as spacer

import {
  chartsCustomizations,
  dataGridCustomizations,
  datePickersCustomizations,
  treeViewCustomizations,
} from '../components/dashboard/theme/customizations';

const xThemeComponents = {
  ...chartsCustomizations,
  ...dataGridCustomizations,
  ...datePickersCustomizations,
  ...treeViewCustomizations,
};

export default function Dashboard(props) {
  return (
    <AppTheme {...props} themeComponents={xThemeComponents}>
      <CssBaseline enableColorScheme />
      {/* Changed flexDirection to 'column' so the AppBar and main content stack vertically */}
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Top AppBar */}
        <AppAppBar />
        {/* Toolbar acts as a spacer with the same height as the AppBar */}
        <Toolbar />
        <Toolbar />
        {/* Main content area */}
        <Box
          component="main"
          sx={(theme) => ({
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: theme.vars
              ? `rgba(${theme.vars.palette.background.defaultChannel} / 1)`
              : alpha(theme.palette.background.default, 1),
          })}
        >
          <Stack
            spacing={2}
            sx={{
              px: 3,
              pt: 2,
              pb: 0,
            }}
          >
            {/* Optional header content */}
          </Stack>
          <Box
            sx={{
              flexGrow: 1,
              overflow: 'auto',
              px: 3, // horizontal padding
              pb: 3, // bottom padding
            }}
          >
            <MainGrid />
          </Box>
        </Box>
      </Box>
    </AppTheme>
  );
}

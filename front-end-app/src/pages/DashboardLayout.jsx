import * as React from 'react';
import { Outlet } from 'react-router-dom';
import { CssBaseline, Box, Toolbar } from '@mui/material';
import { alpha } from '@mui/material/styles';
import AppTheme from '../components/shared-theme/AppTheme.jsx';
import MenuContent from '../components/dashboard/MenuContent'; // Import MenuContent instead of SideMenu
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

export default function DashboardLayout(props) {
  return (
    <AppTheme {...props} themeComponents={xThemeComponents}>
      <CssBaseline enableColorScheme />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Toolbar />
        <Box
          component="main"
          sx={(theme) => ({
            flexGrow: 1,
            backgroundColor: theme.vars
              ? `rgba(${theme.vars.palette.background.defaultChannel} / 1)`
              : alpha(theme.palette.background.default, 1),
            p: 3,
            overflow: 'auto',
          })}
        >
          {/* Render MenuContent at the top left of the dashboard */}
          {/* <Box sx={{ mb: 2, textAlign: 'left' }}>
            <MenuContent />
          </Box> */}
          {/* Nested routes render here */}
          <Outlet />
        </Box>
      </Box>
    </AppTheme>
  );
}

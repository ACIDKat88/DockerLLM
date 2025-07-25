import * as React from 'react';
import { styled } from '@mui/material/styles';
import Avatar from '@mui/material/Avatar';
import MuiDrawer, { drawerClasses } from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import MenuContent from './MenuContent';
import CardAlert from './CardAlert';
import OptionsMenu from './OptionsMenu';

const drawerWidth = 240;

const Drawer = styled(MuiDrawer)(({ theme }) => ({
  width: drawerWidth,
  flexShrink: 0,
  boxSizing: 'border-box',
  mt: 10,
  [`& .${drawerClasses.paper}`]: {
    width: drawerWidth,
    boxSizing: 'border-box',
  },
}));

export default function SideMenu() {
  return (
    <Drawer
      variant="permanent"
      sx={{
        display: { xs: 'none', md: 'block' },
        // Ensure the side menu stays behind the AppAppBar.
        [`& .${drawerClasses.paper}`]: {
          backgroundColor: 'background.paper',
          zIndex: 0,
        },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          p: 1.5,
        }}
      >
        {/* You might include a logo or placeholder here */}
      </Box>
      <Divider />
      {/* Add padding-top to push the buttons down */}
      <Box
        sx={{
          pt: 18, // adjust this value as needed (e.g., theme.spacing(8) for ~64px)
          overflow: 'auto',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <MenuContent />
       {/* <CardAlert /> */}
      </Box>
      {/* <Stack
        direction="row"
        sx={{
          p: 2,
          gap: 1,
          alignItems: 'center',
          borderTop: '1px solid',
          borderColor: 'divider',
        }}
      >
         <Avatar
          sizes="small"
          alt="Test User"
          src="/static/images/avatar/7.jpg"
          sx={{ width: 36, height: 36 }}
        /> 
        <Box sx={{ mr: 'auto' }}>
          <Typography variant="body2" sx={{ fontWeight: 500, lineHeight: '16px' }}>
            Test User
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            test.user@email.com
          </Typography>
        </Box>
        <OptionsMenu />
      </Stack> */}
    </Drawer>
  );
}

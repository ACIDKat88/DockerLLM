import * as React from 'react';
import { alpha, styled } from '@mui/material/styles';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Container from '@mui/material/Container';
import Divider from '@mui/material/Divider';
import MenuItem from '@mui/material/MenuItem';
import Menu from '@mui/material/Menu';
import Drawer from '@mui/material/Drawer';
import MenuIcon from '@mui/icons-material/Menu';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import ColorModeIconDropdown from '../shared-theme/ColorModeIconDropdown.jsx';
import { useNavigate } from 'react-router-dom';
import { logoutUser } from '../../api'; // Adjust import paths as needed

const strat_logo = "/images/US_Strategic_Command_Emblem.png";

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  flexShrink: 0,
  borderRadius: `calc(${theme.shape.borderRadius}px + 8px)`,
  backdropFilter: 'blur(24px)',
  border: '1px solid',
  borderColor: (theme.vars || theme).palette.divider,
  backgroundColor: theme.vars
    ? `rgba(${theme.vars.palette.background.defaultChannel} / 0.4)`
    : alpha(theme.palette.background.default, 0.4),
  boxShadow: (theme.vars || theme).shadows[1],
  padding: '8px 12px',
}));

export default function AppAppBar() {
  const [open, setOpen] = React.useState(false);
  const [dashboardMenuAnchor, setDashboardMenuAnchor] = React.useState(null);
  const [isLoggedIn, setIsLoggedIn] = React.useState(false);
  const [sessionExpired, setSessionExpired] = React.useState(false);
  const navigate = useNavigate();

  // On mount, check if a session token exists.
  React.useEffect(() => {
    const sessionToken = localStorage.getItem('session_token');
    setIsLoggedIn(!!sessionToken);
  }, []);

  const handleLogout = async () => {
    const sessionToken = localStorage.getItem('session_token');
    try {
      // Call the logout API endpoint to invalidate the session on the server.
      await logoutUser(sessionToken);
    } catch (err) {
      console.error("[ERROR] Logout API call failed:", err);
    } finally {
      // Clear local session data and update state.
      localStorage.removeItem('session_token');
      setIsLoggedIn(false);
      navigate('/signin');
    }
  };

  // Set up a periodic session check (every 60 seconds)
  React.useEffect(() => {
    const intervalId = setInterval(async () => {
      const sessionToken = localStorage.getItem('session_token');
      if (sessionToken) {
        try {
          // Use fetchAddedPages as a "ping" endpoint that requires a valid session.
          const response = await fetchAddedPages(sessionToken);
          // If the response indicates an error about session expiration, show alert and logout.
          if (response.error && response.error.toLowerCase().includes('session')) {
            if (!sessionExpired) {
              setSessionExpired(true);
              alert("Your session has expired. Please login again.");
              handleLogout();
            }
          }
        } catch (error) {
          console.error("[ERROR] Session check failed:", error);
          if (!sessionExpired) {
            setSessionExpired(true);
            alert("Your session has expired. Please login again.");
            handleLogout();
          }
        }
      }
    }, 60000); // Check every 60 seconds

    return () => clearInterval(intervalId);
  }, [sessionExpired]);

  const toggleDrawer = (newOpen) => () => {
    setOpen(newOpen);
  };

  return (
    <AppBar
      position="fixed"
      enableColorOnDark
      sx={{
        boxShadow: 0,
        bgcolor: 'transparent',
        backgroundImage: 'none',
        mt: 'calc(var(--template-frame-height, 0px) + 28px)',
      }}
    >
      <Container maxWidth="lg">
        <StyledToolbar variant="dense" disableGutters>
          {/* Left Section - Logo and Navigation Links */}
          <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', px: 0 }}>
            <img
              src={strat_logo}
              alt="Site Logo"
              style={{
                height: '40px',
                marginRight: '16px',
              }}
            />
            <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
              <Button
                variant="text"
                color="info"
                size="small"
                onClick={() => navigate('/home')}
              >
                Chatbot
              </Button>
              {/* Dashboard Button with Drop-down */}
              <Button
                variant="text"
                color="info"
                size="small"
                onClick={(event) => setDashboardMenuAnchor(event.currentTarget)}
              >
                Dashboard
              </Button>
              <Menu
                id="dashboard-menu"
                anchorEl={dashboardMenuAnchor}
                open={Boolean(dashboardMenuAnchor)}
                onClose={() => setDashboardMenuAnchor(null)}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'left',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'left',
                }}
              >
                <MenuItem
                  onClick={() => {
                    navigate('/dashboard/user-analytics');
                    setDashboardMenuAnchor(null);
                  }}
                >
                  User Analytics
                </MenuItem>
              </Menu>
            </Box>
          </Box>
          {/* Right Section - Login/Logout and Preferences */}
          <Box
            sx={{
              display: { xs: 'none', md: 'flex' },
              gap: 1,
              alignItems: 'center',
            }}
          >
            {isLoggedIn ? (
              <Button
                color="primary"
                variant="contained"
                size="small"
                onClick={handleLogout}
              >
                Logout
              </Button>
            ) : (
              <>
                <Button
                  color="primary"
                  variant="text"
                  size="small"
                  onClick={() => navigate('/signin')}
                >
                  Sign in
                </Button>
                <Button
                  color="primary"
                  variant="contained"
                  size="small"
                  onClick={() => navigate('/signup')}
                >
                  Sign up
                </Button>
              </>
            )}
            <ColorModeIconDropdown />
          </Box>
          {/* Mobile Menu */}
          <Box sx={{ display: { xs: 'flex', md: 'none' }, gap: 1 }}>
            <ColorModeIconDropdown size="medium" />
            <IconButton aria-label="Menu button" onClick={toggleDrawer(true)}>
              <MenuIcon />
            </IconButton>
            <Drawer
              anchor="top"
              open={open}
              onClose={toggleDrawer(false)}
              PaperProps={{
                sx: {
                  top: 'var(--template-frame-height, 0px)',
                },
              }}
            >
              <Box sx={{ p: 2, backgroundColor: 'background.default' }}>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <IconButton onClick={toggleDrawer(false)}>
                    <CloseRoundedIcon />
                  </IconButton>
                </Box>
                <MenuItem onClick={() => { navigate('/chat'); setOpen(false); }}>
                  Chatbot
                </MenuItem>
                {/* For mobile, you can choose to navigate directly to Dashboard or implement a similar drop-down */}
                <MenuItem onClick={() => { navigate('/dashboard'); setOpen(false); }}>
                  Dashboard
                </MenuItem>
                <Divider sx={{ my: 3 }} />
                <Divider sx={{ my: 2 }} />
                {isLoggedIn ? (
                  <MenuItem>
                    <Button
                      color="primary"
                      variant="contained"
                      fullWidth
                      onClick={handleLogout}
                    >
                      Logout
                    </Button>
                  </MenuItem>
                ) : (
                  <>
                    <MenuItem>
                      <Button
                        color="primary"
                        variant="outlined"
                        fullWidth
                        onClick={() => { navigate('/signin'); setOpen(false); }}
                      >
                        Sign in
                      </Button>
                    </MenuItem>
                    <MenuItem>
                      <Button
                        color="primary"
                        variant="contained"
                        fullWidth
                        onClick={() => { navigate('/signup'); setOpen(false); }}
                      >
                        Sign up
                      </Button>
                    </MenuItem>
                  </>
                )}
              </Box>
            </Drawer>
          </Box>
        </StyledToolbar>
      </Container>
    </AppBar>
  );
}

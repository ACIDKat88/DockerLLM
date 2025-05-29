import * as React from 'react';
import {
  Box,
  Button,
  Checkbox,
  CssBaseline,
  FormControlLabel,
  FormLabel,
  FormControl,
  TextField,
  Typography,
  Stack,
} from '@mui/material';
import MuiCard from '@mui/material/Card';
import { styled } from '@mui/material/styles';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import ForgotPassword from './ForgotPassword.jsx';
import AppTheme from '../../shared-theme/AppTheme.jsx';
import ColorModeSelect from '../../shared-theme/ColorModeSelect.jsx';
// ─────────────────────────────────────────────────────
// ✅ REPLACE { login } WITH { loginUser } FROM your new API
// ─────────────────────────────────────────────────────
import { loginUser } from '../../../api.js';

// Base64 encoded small placeholder logo
const strat_logo_data = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0MCIgc3Ryb2tlPSIjMDA0ODhBIiBzdHJva2Utd2lkdGg9IjMiIGZpbGw9Im5vbmUiLz48cG9seWdvbiBwb2ludHM9IjUwLDIwIDIwLDgwIDgwLDgwIiBzdHJva2U9IiMwMDQ4OEEiIHN0cm9rZS13aWR0aD0iMyIgZmlsbD0ibm9uZSIvPjxjaXJjbGUgY3g9IjUwIiBjeT0iNTAiIHI9IjEwIiBmaWxsPSIjMDA0ODhBIi8+PC9zdmc+";

const Card = styled(MuiCard)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  width: '100%',
  padding: theme.spacing(4),
  gap: theme.spacing(3),
  margin: 'auto',
  [theme.breakpoints.up('sm')]: {
    maxWidth: '400px',
  },
  boxShadow:
    '0px 5px 15px rgba(0, 0, 0, 0.1), 0px 15px 35px rgba(0, 0, 0, 0.05)',
  ...theme.applyStyles('dark', {
    boxShadow:
      '0px 5px 15px rgba(0, 0, 0, 0.4), 0px 15px 35px rgba(0, 0, 0, 0.2)',
  }),
}));

const SignInContainer = styled(Stack)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.default,
  position: 'relative',
}));

export default function SignIn(props) {
  const [usernameError, setUsernameError] = React.useState(false);
  const [passwordError, setPasswordError] = React.useState(false);
  const [successMessage, setSuccessMessage] = React.useState('');
  const [errorMessage, setErrorMessage] = React.useState('');
  const [forgotPasswordOpen, setForgotPasswordOpen] = React.useState(false);
  const navigate = useNavigate();

  const handleForgotPasswordOpen = () => {
    setForgotPasswordOpen(true);
  };

  const handleForgotPasswordClose = () => {
    setForgotPasswordOpen(false);
  };

  const validateInputs = () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    let isValid = true;

    if (!username || username.length < 3) {
      setUsernameError(true);
      isValid = false;
    } else {
      setUsernameError(false);
    }

    if (!password) {
      setPasswordError(true);
      isValid = false;
    } else {
      setPasswordError(false);
    }

    return isValid;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validateInputs()) return;

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
      const response = await loginUser({ username, password });
      console.log(response);
      
      if (response.session_token) {
        localStorage.setItem('session_token', response.session_token);
        setSuccessMessage('Login successful! Redirecting...');
        // Redirect based on admin flag
        if (response.is_admin) {
          setTimeout(() => navigate('/dashboard/admin'), 1500);
        } else {
          // Redirect non-admins to /chat (or another appropriate route)
          setTimeout(() => navigate('/chat'), 1500);
        }
      } else {
        setErrorMessage(response.error || 'Invalid login credentials.');
      }
    } catch (error) {
      setErrorMessage('An error occurred during login.');
    }
  };

  return (
    <AppTheme {...props}>
      <CssBaseline />
      <SignInContainer>
        <ColorModeSelect sx={{ position: 'fixed', top: '1rem', right: '1rem' }} />
        <Card>
          <img
            src={strat_logo_data}
            alt="Strategic Command Logo"
            style={{
              height: '80px',
              margin: 'auto',
              display: 'block',
              marginBottom: '16px',
            }}
          />
          <Typography component="h1" variant="h4" textAlign="center">
            Sign in
          </Typography>
          <Box
            component="form"
            onSubmit={handleSubmit}
            sx={{ display: 'flex', flexDirection: 'column', width: '100%', gap: 2 }}
          >
            <FormControl>
              <FormLabel>Username</FormLabel>
              <TextField
                id="username"
                error={usernameError}
                helperText={usernameError ? 'At least 3 characters required' : ''}
                placeholder="Enter username"
                variant="outlined"
                fullWidth
              />
            </FormControl>
            <FormControl>
              <FormLabel>Password</FormLabel>
              <TextField
                id="password"
                type="password"
                error={passwordError}
                helperText={passwordError ? 'Password is required' : ''}
                placeholder="Enter password"
                variant="outlined"
                fullWidth
              />
            </FormControl>
            {/* <FormControlLabel control={<Checkbox />} label="Remember me" /> */}
            <Button type="submit" variant="contained" fullWidth>
              Sign in
            </Button>
            <Button onClick={handleForgotPasswordOpen} variant="text" size="small">
              Forgot password?
            </Button>
            {successMessage && (
              <Typography color="success.main" textAlign="center">
                {successMessage}
              </Typography>
            )}
            {errorMessage && (
              <Typography color="error.main" textAlign="center">
                {errorMessage}
              </Typography>
            )}
            <Box textAlign="center" mt={2}>
              <Typography>
                Don&apos;t have an account?{' '}
                <RouterLink to="/signup" style={{ textDecoration: 'none' }}>
                  Sign up
                </RouterLink>
              </Typography>
            </Box>
          </Box>
        </Card>
      </SignInContainer>
      <ForgotPassword open={forgotPasswordOpen} handleClose={handleForgotPasswordClose} />
    </AppTheme>
  );
}

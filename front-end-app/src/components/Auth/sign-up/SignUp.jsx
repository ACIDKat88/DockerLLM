import React, { useState, useEffect } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CssBaseline from "@mui/material/CssBaseline";
import FormLabel from "@mui/material/FormLabel";
import FormControl from "@mui/material/FormControl";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import MenuItem from "@mui/material/MenuItem";
import Card from "@mui/material/Card";
import { styled } from "@mui/material/styles";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import AppTheme from "../../shared-theme/AppTheme.jsx";
import ColorModeSelect from "../../shared-theme/ColorModeSelect.jsx";

// ───────────────────────────────────────────────────────────────
// ✅ Use the new function names: signupUser & fetchOffices
// ───────────────────────────────────────────────────────────────
import { signupUser, fetchOffices } from "../../../api.js";

// Base64 encoded small placeholder logo
const strat_logo_data = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0MCIgc3Ryb2tlPSIjMDA0ODhBIiBzdHJva2Utd2lkdGg9IjMiIGZpbGw9Im5vbmUiLz48cG9seWdvbiBwb2ludHM9IjUwLDIwIDIwLDgwIDgwLDgwIiBzdHJva2U9IiMwMDQ4OEEiIHN0cm9rZS13aWR0aD0iMyIgZmlsbD0ibm9uZSIvPjxjaXJjbGUgY3g9IjUwIiBjeT0iNTAiIHI9IjEwIiBmaWxsPSIjMDA0ODhBIi8+PC9zdmc+";

const StyledCard = styled(Card)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  alignSelf: "center",
  width: "100%",
  padding: theme.spacing(4),
  gap: theme.spacing(2),
  margin: "auto",
  boxShadow:
    "hsla(220, 30%, 5%, 0.05) 0px 5px 15px 0px, hsla(220, 25%, 10%, 0.05) 0px 15px 35px -5px",
  [theme.breakpoints.up("sm")]: {
    width: "450px",
  },
}));

const SignUpContainer = styled(Stack)(({ theme }) => ({
  height: "calc((1 - var(--template-frame-height, 0)) * 100dvh)",
  minHeight: "100%",
  padding: theme.spacing(2),
  [theme.breakpoints.up("sm")]: {
    padding: theme.spacing(4),
  },
}));

export default function SignUp(props) {
  const [usernameError, setUsernameError] = useState(false);
  const [usernameErrorMessage, setUsernameErrorMessage] = useState("");
  const [passwordError, setPasswordError] = useState(false);
  const [passwordErrorMessage, setPasswordErrorMessage] = useState("");
  
  const [officeCodes, setOfficeCodes] = useState([]);
  const [selectedOfficeCode, setSelectedOfficeCode] = useState("");
  const [officeError, setOfficeError] = useState(false);
  const [officeErrorMessage, setOfficeErrorMessage] = useState("");
  
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const navigate = useNavigate();

  // Fetch office codes (with the new function fetchOffices)
  useEffect(() => {
    fetchOffices()
      .then((data) => {
        // The new API returns an array of { office_id, office_code }
        setOfficeCodes(data);
      })
      .catch((error) => {
        console.error("Failed to load office codes:", error);
      });
  }, []);

  const validateInputs = () => {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    let isValid = true;

    if (!username || username.length < 3) {
      setUsernameError(true);
      setUsernameErrorMessage("Username must be at least 3 characters long.");
      isValid = false;
    } else {
      setUsernameError(false);
      setUsernameErrorMessage("");
    }

    if (!password) {
      setPasswordError(true);
      setPasswordErrorMessage("Password cannot be empty.");
      isValid = false;
    } else {
      setPasswordError(false);
      setPasswordErrorMessage("");
    }

    if (!selectedOfficeCode) {
      setOfficeError(true);
      setOfficeErrorMessage("Please select an office code.");
      isValid = false;
    } else {
      setOfficeError(false);
      setOfficeErrorMessage("");
    }

    return isValid;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!validateInputs()) {
      return;
    }

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      // 🔹 Use the updated function, passing an object
      const response = await signupUser({
        username,
        password,
        office_code: selectedOfficeCode,
      });

      if (response.message === "User created successfully") {
        setSuccessMessage("Signup successful! Redirecting to login...");
        setTimeout(() => navigate("/signin"), 2000);
      } else {
        setErrorMessage(response.error || "Signup failed. Please try again.");
      }
    } catch (error) {
      setErrorMessage("An error occurred. Please try again.");
    }
  };

  return (
    <AppTheme {...props}>
      <CssBaseline enableColorScheme />
      <ColorModeSelect sx={{ position: "fixed", top: "1rem", right: "1rem" }} />
      <SignUpContainer direction="column" justifyContent="space-between">
        <StyledCard variant="outlined">
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
          <Typography
            component="h1"
            variant="h4"
            sx={{ width: "100%", fontSize: "clamp(2rem, 10vw, 2.15rem)" }}
          >
            Sign up
          </Typography>
          <Box
            component="form"
            onSubmit={handleSubmit}
            sx={{ display: "flex", flexDirection: "column", gap: 2 }}
          >
            <FormControl>
              <FormLabel htmlFor="username">Username</FormLabel>
              <TextField
                autoComplete="username"
                name="username"
                required
                fullWidth
                id="username"
                placeholder="Enter username"
                error={usernameError}
                helperText={usernameErrorMessage}
              />
            </FormControl>
            <FormControl>
              <FormLabel htmlFor="password">Password</FormLabel>
              <TextField
                required
                fullWidth
                name="password"
                placeholder="••••••"
                type="password"
                id="password"
                autoComplete="new-password"
                error={passwordError}
                helperText={passwordErrorMessage}
              />
            </FormControl>
            <FormControl>
              <FormLabel htmlFor="officeCode">Office Code</FormLabel>
              <TextField
                select
                fullWidth
                required
                value={selectedOfficeCode}
                onChange={(e) => setSelectedOfficeCode(e.target.value)}
                error={officeError}
                helperText={officeErrorMessage}
              >
                <MenuItem value="" disabled>
                  Select an office code
                </MenuItem>
                {officeCodes.map((office) => (
                  <MenuItem key={office.office_id} value={office.office_code}>
                    {office.office_code}
                  </MenuItem>
                ))}
              </TextField>
            </FormControl>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              onClick={validateInputs}
            >
              Sign up
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
            <Box textAlign="center">
              <Typography>
                Already have an account?{" "}
                <RouterLink to="/signin" style={{ textDecoration: "none" }}>
                  Sign in
                </RouterLink>
              </Typography>
            </Box>
          </Box>
        </StyledCard>
      </SignUpContainer>
    </AppTheme>
  );
}

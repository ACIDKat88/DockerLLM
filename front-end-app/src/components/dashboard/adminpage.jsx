import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions, 
  Alert,
  Paper,
  Stack,
  Toolbar,
  Divider,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  Card,
  CardContent,
  Grid,
  CircularProgress
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import CssBaseline from '@mui/material/CssBaseline';
import { alpha, useTheme } from '@mui/material/styles';
import '../shared-theme/AdminPage.css';


// Shared theme and components
import AppTheme from '../shared-theme/AppTheme.jsx';
import {
  chartsCustomizations,
  dataGridCustomizations,
  datePickersCustomizations,
  treeViewCustomizations,
} from './theme/customizations';

// New analytics components
import OfficeQuestionsBarChart from '../dashboard/MainGrid.jsx';
import AnalyticsGrid from '../dashboard/analyticsgrid.jsx';
import ColorModeSelect from '../shared-theme/ColorModeSelect.jsx';
import { logoutUser } from '../../api'; // Adjust import paths as needed
import { useNavigate } from 'react-router-dom';

// Import Recharts components needed for the new chart
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'; // <-- Added Recharts
import DatasetCosineChart from '../dashboard/DatasetCosineChart';
import AverageCosineCard from '../dashboard/AverageCosineCard';
import ModelAccuracyChart from '../dashboard/ModelAccuracyChart';
import RagasMetricsCard from './RagasMetricsCard';


const xThemeComponents = {
  ...chartsCustomizations,
  ...dataGridCustomizations,
  ...datePickersCustomizations,
  ...treeViewCustomizations,
};

export const BASE_URL = "https://j1chatbotbeta.usgovvirginia.cloudapp.usgovcloudapi.net";

const getAuthHeaders = (sessionToken) => ({
  "Content-Type": "application/json",
  "Authorization": sessionToken,
});



const AdminUserManagement = (props) => {
  // State for user management
  const [users, setUsers] = useState([]);
  const sessionToken = localStorage.getItem("session_token") || "";
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [offices, setOffices] = useState([]);
  const [pendingReassignments, setPendingReassignments] = useState({});
  
  // State for password change dialog
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // State for analytics
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [officeChartData, setOfficeChartData] = useState([]);
  const [feedbackChartData, setFeedbackChartData] = useState([]);
  const [averageElapsedTime, setAverageElapsedTime] = useState(null);
  const [analyticsError, setAnalyticsError] = useState(null);
  const [analytics, setAnalytics] = useState([]);

  // States for creating a new user
  const [newUserData, setNewUserData] = useState({
    username: '',
    password: '',
    office_code: ''
  });
  const [creationError, setCreationError] = useState(null);
  const [creationSuccess, setCreationSuccess] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = React.useState(!!localStorage.getItem("session_token"));
  const navigate = useNavigate();
  
    const handleLogout = async () => {
      try {
        await logoutUser(localStorage.getItem("session_token"));
      } catch (error) {
        console.error("Logout error:", error);
      }
      localStorage.removeItem("session_token");
      setIsLoggedIn(false);
      navigate("/signin");
    };

  const theme = useTheme();
  const chartTextColor = theme.palette.text.primary;
  const chartGridColor = theme.palette.divider;
  const chartTooltipBg = theme.palette.background.paper;
  const feedbackBarColor = theme.palette.secondary.main;

  // Fetch users from the admin GET endpoint
  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      console.log("Fetching users...");
      // Add a cache-busting parameter to ensure we get fresh data
      const response = await axios.get(`${BASE_URL}/api/admin?cb=${new Date().getTime()}`, {
        headers: getAuthHeaders(sessionToken),
      });
      
      console.log("Users fetched successfully:", response.data);
      setUsers(response.data.users || []);
    } catch (error) {
      console.error("Error fetching users:", error);
      console.error("Error details:", error.response?.data || "No response data");
      alert("Failed to fetch users. Please check the console for details.");
    }
    setLoadingUsers(false);
  };

  // Fetch offices from the admin GET endpoint
  const fetchOffices = async () => {
    try {
      const response = await axios.get(`${BASE_URL}/api/offices`, {
        headers: getAuthHeaders(sessionToken),
      });
      setOffices(response.data || []);
    } catch (error) {
      console.error("Error fetching offices:", error);
      setOffices([]); // Set to empty array on error
    }
  };

  // Fetch and process analytics data
  const fetchAnalyticsData = async () => {
      setAnalyticsLoading(true);
      setAnalyticsError(null);
      try {
          const response = await axios.get(`${BASE_URL}/api/analytics?cb=${new Date().getTime()}`, {
              headers: getAuthHeaders(sessionToken),
          });
          const analytics = response.data; // Expecting an array of records
          console.log("Fetched Analytics Data:", analytics); // <-- Log raw data
          
          // Store the full analytics data for the new components
          setAnalytics(analytics);
          console.log("Stored Analytics State:", analytics); // <-- Log state after setting

          if (!Array.isArray(analytics)) {
            throw new Error("Invalid analytics data format received.");
          }

          // Process data for Office Questions Bar Chart
          const officeCounts = {};
          analytics.forEach((record) => {
            if (record.office_code && record.question && record.question.trim() !== "") {
                officeCounts[record.office_code] = (officeCounts[record.office_code] || 0) + 1;
            }
          });
          const newOfficeChartData = Object.keys(officeCounts).map((office_code) => ({
            office_id: office_code,
            count: officeCounts[office_code],
          }));
          setOfficeChartData(newOfficeChartData);

          // Process data for Feedback State Bar Chart
          const feedbackCounts = {};
          analytics.forEach((record) => {
              const state = record.feedback || 'N/A';
              feedbackCounts[state] = (feedbackCounts[state] || 0) + 1;
          });
          const newFeedbackChartData = Object.keys(feedbackCounts).map((state) => ({
              name: state,
              count: feedbackCounts[state],
          }));
          setFeedbackChartData(newFeedbackChartData);

          // Process data for Average Elapsed Time
          let totalElapsedTime = 0;
          let validRecordsCount = 0;
          analytics.forEach((record) => {
              if (typeof record.response_time === 'number' && !isNaN(record.response_time)) {
                  totalElapsedTime += record.response_time;
                  validRecordsCount++;
              }
          });
          const newAverageTime = validRecordsCount > 0 ? (totalElapsedTime / validRecordsCount).toFixed(2) : 'N/A';
          setAverageElapsedTime(newAverageTime);

      } catch (error) {
          console.error("Error fetching or processing analytics data:", error);
          setAnalyticsError("Failed to load analytics data.");
          setOfficeChartData([]);
          setFeedbackChartData([]);
          setAverageElapsedTime(null);
          setAnalytics([]);
      } finally {
          setAnalyticsLoading(false);
      }
  };

  useEffect(() => {
    setIsLoggedIn(!!sessionToken);
    if (sessionToken) {
        fetchUsers();
        fetchOffices();
        fetchAnalyticsData(); // Initial fetch
        // Set up polling for analytics data
        const interval = setInterval(fetchAnalyticsData, 30000); // Poll every 30 seconds
        return () => clearInterval(interval); // Cleanup interval on component unmount
    } else {
        // Clear analytics data if logged out
        setOfficeChartData([]);
        setFeedbackChartData([]);
        setAverageElapsedTime(null);
        setAnalyticsLoading(false);
    }
  }, [sessionToken]);

  // Toggle disabled status for a user
  const handleToggleDisable = async (user) => {
    const action = user.disabled ? "enable" : "disable";
    console.log(`Attempting to ${action} user:`, user);
    console.log("User disabled status before action:", user.disabled);
    
    try {
      console.log("Sending request payload:", {
        action,
        target_user_id: user.user_id,
      });
      
      const response = await axios.post(`${BASE_URL}/api/admin`, {
        action,
        target_user_id: user.user_id,
      }, {
        headers: getAuthHeaders(sessionToken),
      });
      
      console.log(`${action} action response:`, response.data);
      
      // Force refresh the user list to show updated status
      fetchUsers();
    } catch (error) {
      console.error(`Error performing ${action} action:`, error);
      console.error("Error details:", error.response?.data || "No response data");
      alert(`Failed to ${action} user. Please check the console for details.`);
    }
  };

  // *** ADDED: Handler for toggling admin status ***
  const handleToggleAdmin = async (user) => {
    const action = "toggle_admin";
    try {
      await axios.post(`${BASE_URL}/api/admin`, {
        action,
        target_user_id: user.user_id,
      }, {
        headers: getAuthHeaders(sessionToken),
      });
      fetchUsers(); // Refresh user list
    } catch (error) {
      console.error(`Error performing ${action} action:`, error);
      // Optionally show an error message
    }
  };

  // Handle opening the password change dialog
  const handleOpenPasswordDialog = (user) => {
    setSelectedUser(user);
    setNewPassword('');
    setConfirmPassword('');
    setPasswordError('');
    setPasswordSuccess('');
    setPasswordDialogOpen(true);
  };

  // Handle changing a user's password
  const handleChangePassword = async () => {
    // Input validation
    if (!newPassword) {
      setPasswordError("Password cannot be empty");
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setPasswordError("Passwords do not match");
      return;
    }

    try {
      const response = await axios.post(`${BASE_URL}/api/admin/change_password`, {
        target_user_id: selectedUser.user_id,
        new_password: newPassword
      }, {
        headers: getAuthHeaders(sessionToken),
      });
      
      setPasswordSuccess("Password changed successfully");
      // Clear the form after successful update
      setNewPassword('');
      setConfirmPassword('');
      
      // Close dialog after a short delay to show the success message
      setTimeout(() => {
        setPasswordDialogOpen(false);
      }, 1500);
      
    } catch (error) {
      console.error("Error changing password:", error);
      setPasswordError(error.response?.data?.detail || "Error changing password");
    }
  };

  // Handle new user form input changes
  const handleNewUserChange = (e) => {
    const { name, value } = e.target;
    setNewUserData((prev) => ({ ...prev, [name]: value }));
  };

  // Create a new regular user (non-admin) via admin endpoint
  const handleCreateUser = async (e) => {
    e.preventDefault();
    setCreationError(null);
    setCreationSuccess(null);
    const { username, password, office_code } = newUserData;
    if (!username || !password || !office_code) {
      setCreationError("All fields are required.");
      return;
    }
    try {
      await axios.post(`${BASE_URL}/api/admin/create_user`, newUserData, {
        headers: getAuthHeaders(sessionToken),
      });
      setCreationSuccess("User created successfully.");
      setNewUserData({ username: '', password: '', office_code: '' });
      fetchUsers();
    } catch (error) {
      console.error("Error creating user:", error);
      setCreationError(error.response?.data?.detail || "Error creating user.");
    }
  };

  // Handle inline office reassignment
  const handleInlineReassign = async (userId, newOfficeCode) => {
    if (!newOfficeCode) return; // Should not happen with select, but safety check
    try {
      await axios.post(`${BASE_URL}/api/admin`, {
        action: "reassign",
        target_user_id: userId,
        office_code: newOfficeCode,
      }, {
        headers: getAuthHeaders(sessionToken),
      });
      // Optionally show a success snackbar/message here
      fetchUsers(); // Refresh user list to show the change
    } catch (error) {
      console.error("Error reassigning office inline:", error);
      // Optionally show an error snackbar/message here
      // Revert optimistic UI update if implemented
    }
  };

  // *** ADDED: Handler for select change to update pending state ***
  const handlePendingReassignChange = (userId, newOfficeCode) => {
    setPendingReassignments(prev => ({
      ...prev,
      [userId]: newOfficeCode,
    }));
  };

  // *** UPDATED: Handler for confirming the reassignment ***
  const handleConfirmReassign = async (userId) => {
    const newOfficeCode = pendingReassignments[userId];
    const user = users.find(u => u.user_id === userId); // Find user to compare original office code

    // Check if a new code is selected and it's different from the current one
    if (!newOfficeCode || !user || newOfficeCode === user.office_code) {
      console.log("No change or invalid state for reassignment.");
      return; // No change to confirm
    }

    try {
      await axios.post(`${BASE_URL}/api/admin`, {
        action: "reassign",
        target_user_id: userId,
        office_code: newOfficeCode,
      }, {
        headers: getAuthHeaders(sessionToken),
      });
      fetchUsers(); // Refresh user list to show the change
      // Clear the pending state for this user on success
      setPendingReassignments(prev => {
        const next = { ...prev };
        delete next[userId];
        return next;
      });
      // Optionally show a success snackbar/message here
    } catch (error) {
      console.error("Error confirming office reassignment:", error);
      // Optionally show an error snackbar/message here
    }
  };

  // Define columns for the DataGrid listing users
  const columns = [
    {
      field: 'username',
      headerName: 'Username',
      flex: 0.7,
      minWidth: 120,
      headerAlign: 'center',
      align: 'center',
    },
    {
      field: 'office_code',
      headerName: 'Office Code',
      flex: 0.7,
      minWidth: 120,
      headerAlign: 'center',
      align: 'center',
    },
    {
      field: 'is_admin',
      headerName: 'Admin',
      flex: 1,
      headerAlign: 'center',
      align: 'center',
      renderCell: (params) => (params.value ? "Yes" : "No"),
    },
    {
      field: 'disabled',
      headerName: 'Disabled',
      flex: 0.5,
      minWidth: 100,
      headerAlign: 'center',
      align: 'center',
      renderCell: (params) => (params.value ? "Yes" : "No"),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      flex: 3,
      minWidth: 450,
      sortable: false,
      headerAlign: 'center',
      align: 'center',
      renderCell: (params) => {
        const user = params.row;
        const pendingValue = pendingReassignments[user.user_id];
        const selectValue = pendingValue !== undefined ? pendingValue : (user.office_code || "");
        const hasPendingChange = pendingValue !== undefined && pendingValue !== user.office_code;

        return (
          <Box sx={{
            display: 'flex', 
            flexWrap: 'wrap',
            alignItems: 'center', 
            justifyContent: 'center',
            gap: 1, 
            width: '100%',
            p: 1,
            py: 0.5,
            px: 0.5
          }}>
            {/* Disable/Enable Button - Using theme */}
            <Button
              variant="contained"
              size="small"
              color={user.disabled ? "success" : "warning"} // Use theme colors
              onClick={(e) => {
                e.stopPropagation(); // Prevent click from bubbling up
                handleToggleDisable(user);
              }}
              sx={(theme) => ({
                minWidth: '100px',
                textTransform: 'none',
                fontSize: { xs: '0.7rem', sm: '0.8rem' },
              })}
            >
              {user.disabled ? "Enable" : "Disable"}
            </Button>

            {/* Make/Revoke Admin Button - Using theme */}
            <Button
              variant="contained"
              size="small"
              color={user.is_admin ? "error" : "secondary"} // Use theme colors
              onClick={() => handleToggleAdmin(user)}
              sx={{ 
                minWidth: '100px', 
                textTransform: 'none',
                fontSize: { xs: '0.7rem', sm: '0.8rem' },
              }}
            >
              {user.is_admin ? "Revoke Admin" : "Make Admin"}
            </Button>

            {/* Office Select Dropdown - Using theme */}
            <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                <Select
                    id={`reassign-select-${user.user_id}`}
                    value={selectValue}
                    onChange={(e) => handlePendingReassignChange(user.user_id, e.target.value)}
                    displayEmpty
                    sx={(theme) => ({
                        backgroundColor: theme.palette.action.selected,
                        color: theme.palette.text.primary,
                        textTransform: 'none',
                        borderRadius: '4px',
                        height: '36.5px',
                        fontSize: { xs: '0.7rem', sm: '0.8rem' },
                        '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
                        '&:hover': {
                            backgroundColor: theme.palette.action.hover,
                        },
                        '&.Mui-focused .MuiOutlinedInput-notchedOutline': { border: 'none' },
                        '& .MuiSelect-icon': { color: theme.palette.action.active },
                        '& .MuiSelect-select': {
                           paddingTop: '8px', paddingBottom: '8px', paddingLeft: '16px', paddingRight: '32px !important',
                        },
                    })}
                    MenuProps={{
                        PaperProps: {
                            sx: (theme) => ({
                                backgroundColor: theme.palette.background.paper,
                                color: theme.palette.text.primary,
                            }),
                        },
                    }}
                >
                    <MenuItem value="" disabled sx={{ opacity: 0.5 }}>
                        <em>Reassign Office</em>
                    </MenuItem>
                    {offices.map((office) => (
                        <MenuItem
                            key={office.office_code} value={office.office_code}
                            sx={(theme) => ({
                                '&:hover': {
                                    backgroundColor: theme.palette.action.hover,
                                },
                                '&.Mui-selected': {
                                    backgroundColor: alpha(theme.palette.primary.main, theme.palette.action.selectedOpacity),
                                },
                                '&.Mui-selected:hover': {
                                    backgroundColor: alpha(theme.palette.primary.main, theme.palette.action.selectedOpacity + theme.palette.action.hoverOpacity),
                                }
                            })}
                        >
                            {office.office_code}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>

            {/* Confirm Reassign Button - Using theme */}
            <Button
              variant="contained" size="small"
              color="success" // Use success color when enabled
              onClick={() => handleConfirmReassign(user.user_id)}
              disabled={!hasPendingChange}
              sx={(theme) => ({
                minWidth: '100px',
                textTransform: 'none',
                fontSize: { xs: '0.7rem', sm: '0.8rem' },
                backgroundColor: hasPendingChange ? undefined : theme.palette.action.disabledBackground,
                color: hasPendingChange ? undefined : theme.palette.action.disabled,
                '&:hover': {
                  backgroundColor: hasPendingChange ? theme.palette.success.dark : undefined,
                }
              })}
            >
              {hasPendingChange ? `Confirm: ${pendingValue}` : `Current: ${user.office_code || 'N/A'}`}
            </Button>
            
            {/* Reset Password Button */}
            <Button
              variant="contained"
              size="small"
              sx={{ 
                minWidth: '100px', 
                textTransform: 'none',
                fontSize: { xs: '0.7rem', sm: '0.8rem' },
                bgcolor: '#5e35b1', // Dark purple background
                color: 'white',     // White text
                '&:hover': {
                  bgcolor: 'white', // White background on hover
                  color: 'black',   // Black text on hover
                  boxShadow: '0px 2px 4px rgba(0,0,0,0.2)'
                }
              }}
              onClick={() => handleOpenPasswordDialog(user)}
            >
              Reset Password
            </Button>
          </Box>
        );
      },
    },
  ];
  

  return (
    <AppTheme {...props} themeComponents={xThemeComponents}>
      <CssBaseline enableColorScheme />
      <Box sx={{position: 'fixed', top: '1rem', right: '1rem', display: 'flex', alignItems: 'center', gap: 2, zIndex: 1300 }}>
        <ColorModeSelect />
        {isLoggedIn && (
          <Button color="inherit" variant="outlined" size="small" onClick={handleLogout}
            sx={{ textTransform: 'none' }}
          >
            Logout
          </Button>
        )}
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Box
          component="main"
          sx={(theme) => ({
            flexGrow: 1, display: 'flex', flexDirection: 'column',
            backgroundColor: theme.palette.background.default,
            pt: '5rem'
          })}
        >
          <Stack spacing={2} sx={{ px: 3, pb: 0 }}>
            <Typography variant="h4" gutterBottom>
              Admin User Management & Analytics
            </Typography>
          </Stack>
          <Box sx={{ flexGrow: 1, overflow: 'auto', px: 3, pb: 3 }}>
            {/* New User Creation Section */}
            <Paper sx={{ p: 2, mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                Create New User
              </Typography>
              {creationError && <Alert severity="error" sx={{ mb: 1 }}>{creationError}</Alert>}
              {creationSuccess && <Alert severity="success" sx={{ mb: 1 }}>{creationSuccess}</Alert>}
              <Box component="form" onSubmit={handleCreateUser} noValidate sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                <TextField label="Username" name="username" value={newUserData.username} onChange={handleNewUserChange} required variant="outlined" size="small"/>
                <TextField label="Password" name="password" type="password" value={newUserData.password} onChange={handleNewUserChange} required variant="outlined" size="small"/>
                <FormControl variant="outlined" size="small" sx={{ minWidth: 150 }} required>
                  <InputLabel id="create-user-office-label">Office Code</InputLabel>
                  <Select
                    labelId="create-user-office-label"
                    id="create-user-office-select"
                    name="office_code"
                    value={newUserData.office_code}
                    onChange={handleNewUserChange}
                    label="Office Code"
                  >
                    <MenuItem value="" disabled>
                      <em>Select Office</em>
                    </MenuItem>
                    {offices.map((office) => (
                      <MenuItem key={office.office_code} value={office.office_code}>
                        {office.office_code}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    sx={{ textTransform: 'none' }}
                    >
                    Create User
                    </Button>
              </Box>
            </Paper>

            {/* User Management Section */}
            <Paper sx={{ p: 2, mb: 4 }}>
              <Typography variant="h6" align="center" sx={{ mb: 2 }}>User Management</Typography>
              <Box sx={{ height: 400, width: '100%', display: 'flex', overflow: 'auto' }}>
                  <DataGrid
                      rows={users}
                      columns={columns}
                      getRowId={(row) => row.user_id}
                      loading={loadingUsers}
                      pageSize={10}
                      rowsPerPageOptions={[10, 20, 50]}
                      sx={{ 
                        flexGrow: 1,
                        '& .MuiDataGrid-cell': {
                          whiteSpace: 'normal',
                          padding: '8px',
                        },
                        '& .MuiDataGrid-columnHeader': {
                          whiteSpace: 'normal',
                          lineHeight: '1.2',
                        }
                      }}
                  />
              </Box>
            </Paper>

            {/* Analytics Section */}
            <Paper sx={{ p: 2, mb: 4 }}>
              <Typography variant="h6" align="center" gutterBottom sx={{ mb: 2 }}>Analytics Overview</Typography>
              {analyticsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
                  <CircularProgress />
                </Box>
              ) : analyticsError ? (
                 <Alert severity="error" sx={{ mt: 2 }}>{analyticsError}</Alert>
              ) : (
                <Grid container spacing={3} sx={{ mt: 0 }}>
                  {/* ROW 1: Cards */}
                  {/* Average Response Time Card */}
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      <Card sx={{ height: '100%', p: 2, width: '100%', maxWidth: '500px' }}>
                        <CardContent>
                          <Typography variant="h6" align="center" gutterBottom>
                            Average Response Time
                          </Typography>
                          <Typography variant="h4" component="div" align="center" sx={{ mt: 2 }}>
                            {averageElapsedTime ?? 'N/A'}
                            {typeof averageElapsedTime === 'string' && averageElapsedTime !== 'N/A' ? ' s' : ''}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Box>
                  </Grid>
                  
                  {/* Average Accuracy Card */}
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      <Box sx={{ width: '100%', maxWidth: '500px' }}>
                        <AverageCosineCard analyticsData={analytics} />
                      </Box>
                    </Box>
                  </Grid>
                  
                  {/* ROW 2: Dataset and Model Charts */}
                  {/* Dataset Cosine Similarity Chart */}
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      <Box sx={{ width: '100%', maxWidth: '650px' }}>
                        <DatasetCosineChart analyticsData={analytics} />
                      </Box>
                    </Box>
                  </Grid>
                  
                  {/* Model Accuracy Chart */}
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      <Box sx={{ width: '100%', maxWidth: '650px' }}>
                        <ModelAccuracyChart analyticsData={analytics} />
                      </Box>
                    </Box>
                  </Grid>
                  
                  {/* ROW 3: Feedback and Office Charts */}
                  {/* Feedback State Chart */}
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      <Card sx={{ height: '100%', p: 2, width: '100%', maxWidth: '650px' }}>
                        <CardContent>
                          <Typography variant="h6" align="center" gutterBottom>
                            Questions Count by Feedback State
                          </Typography>
                          
                          {feedbackChartData.length === 0 ? (
                            <Typography variant="body1" align="center" sx={{ mt: 4 }}>
                              No feedback data available.
                            </Typography>
                          ) : (
                            <Box sx={{ width: '100%', height: 300, mt: 2 }}>
                              <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={feedbackChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                  <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} />
                                  <XAxis dataKey="name" stroke={chartTextColor} tick={{ fill: chartTextColor }} />
                                  <YAxis allowDecimals={false} stroke={chartTextColor} tick={{ fill: chartTextColor }} />
                                  <Tooltip
                                    contentStyle={{ backgroundColor: chartTooltipBg, border: `1px solid ${chartGridColor}` }}
                                    labelStyle={{ color: chartTextColor }}
                                    itemStyle={{ color: chartTextColor }}
                                   />
                                  <Legend wrapperStyle={{ color: chartTextColor }} />
                                  <Bar dataKey="count" fill={feedbackBarColor} name="Feedback Count" />
                                </BarChart>
                              </ResponsiveContainer>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </Box>
                  </Grid>
                  
                  {/* Office Questions Chart */}
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      <Box sx={{ width: '100%', maxWidth: '650px' }}>
                        <OfficeQuestionsBarChart chartData={officeChartData} />
                      </Box>
                    </Box>
                  </Grid>

                  {/* RAGAS Metrics Card - Centered and 30% larger */}
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      <Box sx={{ width: '100%', maxWidth: '1050px' }}>
                        <RagasMetricsCard />
                      </Box>
                    </Box>
                  </Grid>
                </Grid>
              )}
            </Paper>

            {/* Analytics Details Table Section */}
            <Paper sx={{ p: 2, mb: 4 }}>
              <Typography variant="h6" align="center" gutterBottom sx={{ mb: 2 }}>Analytics Details</Typography>
              {console.log("Passing analytics to AnalyticsGrid:", analytics)} {/* <-- Log props for grid */}
              <AnalyticsGrid /> { /* Check if AnalyticsGrid needs the prop passed */}
            </Paper>

          </Box>
        </Box>
      </Box>

      <Divider sx={{ mt: 'auto', width: '100%' }} />
      <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 2 }}>
        Admin Dashboard - Powered by j1chat
      </Typography>

      {/* Password Change Dialog */}
      <Dialog open={passwordDialogOpen} onClose={() => setPasswordDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Change Password for {selectedUser?.username}
        </DialogTitle>
        <DialogContent>
          {passwordError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {passwordError}
            </Alert>
          )}
          {passwordSuccess && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {passwordSuccess}
            </Alert>
          )}
          <TextField
            margin="dense"
            label="New Password"
            type="password"
            fullWidth
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            margin="dense"
            label="Confirm Password"
            type="password"
            fullWidth
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleChangePassword} variant="contained" color="primary">
            Change Password
          </Button>
        </DialogActions>
      </Dialog>
    </AppTheme>
  );
};

export default AdminUserManagement;

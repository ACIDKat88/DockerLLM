import React, { useState, useEffect } from 'react';
import { Grid, Typography, Box } from '@mui/material';
import { fetchOfficeUsers, fetchOfficeUserInteractions } from '../../api';
import UserDataGrid_UsersList from './UserDataGrid_UsersList';
import UserDataGrid_UserActivity from './UserDataGrid_UserActivity';
import UserArticleFilter from './UserArticleFilter';

/**
 * UserAnalytics
 * A page component that displays office user analytics.
 * It shows a filter at the top to select users and article titles,
 * then displays two tables: one for office users and one for user activity,
 * filtered accordingly.
 */
export default function UserAnalytics() {
  const [users, setUsers] = useState([]);
  const [userInteractions, setUserInteractions] = useState([]);

  // These state variables store the filtered results.
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [filteredUserInteractions, setFilteredUserInteractions] = useState([]);

  // States to store currently applied filter values.
  const [filterUsers, setFilterUsers] = useState([]);
  const [filterArticles, setFilterArticles] = useState([]);

  const sessionToken = localStorage.getItem("session_token") || "";

  // Fetch office users from the API.
  useEffect(() => {
    fetchOfficeUsers(sessionToken)
      .then(response => {
        const data = response.data.users || [];
        setUsers(data);
        // Initially, no filters are applied.
        setFilteredUsers(data);
      })
      .catch(error => {
        console.error("Error fetching office users:", error);
      });
  }, [sessionToken]);

  // Fetch office user interactions from the API.
  useEffect(() => {
    fetchOfficeUserInteractions(sessionToken)
      .then(response => {
        const data = response.data.user_interactions || [];
        setUserInteractions(data);
        setFilteredUserInteractions(data);
      })
      .catch(error => {
        console.error("Error fetching user interactions:", error);
      });
  }, [sessionToken]);

  // When filters are applied, update the filtered arrays.
  const handleApplyFilters = (selectedUsers, selectedArticleTitles) => {
    setFilterUsers(selectedUsers);
    setFilterArticles(selectedArticleTitles);

    // Filter users by username if filter list is non-empty.
    const newFilteredUsers =
      selectedUsers.length > 0
        ? users.filter(u => selectedUsers.includes(u.username))
        : users;
    setFilteredUsers(newFilteredUsers);

    // Filter interactions by username and article title.
    let newFilteredInteractions = userInteractions;
    if (selectedUsers.length > 0) {
      newFilteredInteractions = newFilteredInteractions.filter(interaction =>
        selectedUsers.includes(interaction.username)
      );
    }
    if (selectedArticleTitles.length > 0) {
      newFilteredInteractions = newFilteredInteractions.filter(interaction =>
        selectedArticleTitles.some(title =>
          interaction.title.toLowerCase().includes(title.toLowerCase())
        )
      );
    }
    setFilteredUserInteractions(newFilteredInteractions);
  };

  // When filters are cleared, reset to the original data.
  const handleClearFilters = () => {
    setFilterUsers([]);
    setFilterArticles([]);
    setFilteredUsers(users);
    setFilteredUserInteractions(userInteractions);
  };

  const fixedWidth = 1000;

  return (
    <Grid container spacing={3} sx={{ mt: 4 }}>
      {/* Filter Section at the Top */}
      <Grid item xs={12}>
        <UserArticleFilter
          finalUserFilters={filterUsers}
          finalArticleFilters={filterArticles}
          onApplyFilters={handleApplyFilters}
          onClearFilters={handleClearFilters}
        />
      </Grid>

      {/* Office Users Table */}
      <Grid item xs={12}>
        <Typography variant="h6" sx={{ mb: 1, textAlign: 'center' }}>
          Office Users
        </Typography>
        <Box
          sx={{
            width: fixedWidth,
            mx: 'auto',
            overflow: 'auto',
            border: '1px solid #ccc',
            borderRadius: 1,
            p: 2,
          }}
        >
          <UserDataGrid_UsersList rows={filteredUsers} />
        </Box>
      </Grid>

      {/* User Activity Table */}
      <Grid item xs={12}>
        <Typography variant="h6" sx={{ mb: 1, textAlign: 'center' }}>
          User Activity
        </Typography>
        <Box
          sx={{
            width: fixedWidth,
            mx: 'auto',
            overflow: 'auto',
            border: '1px solid #ccc',
            borderRadius: 1,
            p: 2,
          }}
        >
          <UserDataGrid_UserActivity rows={filteredUserInteractions} />
        </Box>
      </Grid>
    </Grid>
  );
}

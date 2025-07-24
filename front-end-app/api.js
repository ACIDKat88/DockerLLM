import axios from 'axios';
import { useEffect } from 'react';

export const BASE_URL = "https://docker-llm-frontend--6b5efca2ab.jobs.scottdc.org.apolo.scottdata.ai";

/**
 * handleResponse
 * Logs the response status and parses the JSON payload if the response is OK,
 * otherwise throws an error with the server's error message (if available).
 */
async function handleResponse(response) {
  console.log(`[DEBUG] Received response with status: ${response.status}`);

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch (e) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    console.error("[ERROR] Server responded with:", errorData);
    throw new Error(errorData.error || `HTTP error: ${response.status}`);
  }
  return response.json();
}

export async function updateUsername(newUsername, sessionToken) {
  console.log("[DEBUG] Updating username to:", newUsername);
  return fetch(`${BASE_URL}/api/username`, {
    method: "POST",
    headers: getAuthHeaders(sessionToken),
    body: JSON.stringify({ username: newUsername }),
  })
    .then(handleResponse)
    .catch(handleError);
}

export async function adminCreateUser(payload, sessionToken) {
  console.log("[DEBUG] Admin creating user with payload:", payload);
  return fetch(`${BASE_URL}/api/admin/create_user`, {
    method: "POST",
    headers: getAuthHeaders(sessionToken),
    body: JSON.stringify(payload),
  })
    .then(handleResponse)
    .catch(handleError);
}

/**
 * adminChangePassword
 * POST /api/admin/change_password
 * 
 * Changes a user's password (admin only)
 * 
 * @param {object} payload - { target_user_id, new_password }
 * @param {string} sessionToken - Admin session token
 * @returns {object} - Response from the server
 */
export async function adminChangePassword(payload, sessionToken) {
  console.log("[DEBUG] Admin changing password for user:", payload.target_user_id);
  return fetch(`${BASE_URL}/api/admin/change_password`, {
    method: "POST",
    headers: getAuthHeaders(sessionToken),
    body: JSON.stringify(payload),
  })
    .then(handleResponse)
    .catch(handleError);
}

/**
 * handleError
 * Logs the error in console and re-throws it for further handling upstream.
 */
function handleError(error) {
  console.error("[ERROR] Network or parsing error:", error);
  throw error;
}

/**
 * getAuthHeaders
 * Helper to append the session token to the request headers if provided.
 */
function getAuthHeaders(sessionToken) {
  const headers = {
    "Content-Type": "application/json",
  };
  if (sessionToken) {
    headers["Authorization"] = sessionToken;
  }
  return headers;
}

/**
 * fetchOffices
 * GET /api/offices
 *
 * Note: The provided FastAPI backend does not implement /api/offices.
 * This function returns dummy data for compatibility.
 */
// api.js

export async function fetchOffices() {
  try {
    const response = await fetch(`${BASE_URL}/api/offices`);
    if (!response.ok) {
      throw new Error('Failed to fetch office codes');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching office codes:', error);
    throw error;
  }
}
/**
 * updateOffice
 * PUT /api/offices
 *
 * Updates an office's details.
 * 
 * @param {object} officeData - The office data to update (e.g., { office_code: "XYZ", office_id: "123", ... }).
 * @param {string} sessionToken - The current session token.
 * @returns {object} - The updated office data or a confirmation message.
 */
export async function updateOffice(officeData, sessionToken) {
  console.log("[DEBUG] Updating office with data:", officeData);
  return fetch(`${BASE_URL}/offices`, {
    method: "PUT",
    headers: getAuthHeaders(sessionToken),
    body: JSON.stringify(officeData),
  })
    .then(handleResponse)
    .catch(handleError);
}

/**
 * fetchUserNames
 * GET /api/username
 *
 * Note: The provided FastAPI backend does not implement /api/username.
 * This function returns dummy data for compatibility.
 */
export function fetchUserNames() {
  console.log("[DEBUG] fetchUserNames called, but /api/username endpoint is not implemented in backend. Returning dummy data.");
  // Return dummy user names data
  return Promise.resolve({ username: [] });
}

/**
 * fetchChatMetrics
 * Returns dummy chat metrics data.
 */
export const fetchChatMetrics = (sessionToken) => {
  console.log("[DEBUG] fetchChatMetrics called. Returning dummy data.");
  return Promise.resolve({ metrics: {} });
};

/**
 * signupUser
 * POST /signup
 *
 * @param {object} payload - { username, password, office_code }
 */
export async function signupUser(payload) {
  console.log("[DEBUG] Signing up user with payload:", payload);
  return fetch(`${BASE_URL}/api/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then(handleResponse)
    .catch(handleError);
}

/**
 * loginUser
 * POST /login
 *
 * @param {object} payload - { username, password }
 * @returns {object} - { message, session_token }
 */
export async function loginUser(payload) {
  console.log("[DEBUG] Logging in user with payload:", payload);
  return fetch(`${BASE_URL}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then(handleResponse)
    .catch(handleError);
}

/**
 * logoutUser
 * POST /logout
 *
 * @param {string} sessionToken
 * @returns {object} - Response from the server
 */
export async function logoutUser(sessionToken) {
  console.log("[DEBUG] Logging out user");
  
  return fetch(`${BASE_URL}/api/logout`, {
    method: "POST",
    headers: getAuthHeaders(sessionToken)
  })
    .then(handleResponse)
    .catch(handleError);
}

/**
 * fetchOfficeUsers
 * GET /api/office_users
 *
 * Note: The provided FastAPI backend does not implement /api/office_users.
 * This function returns dummy data for compatibility.
 *
 * @param {string} sessionToken - The current session token.
 */
export function fetchOfficeUsers(sessionToken) {
  console.log("[DEBUG] fetchOfficeUsers called, but /api/office_users endpoint is not implemented in backend. Returning dummy data.");
  // Return dummy office users data
  return Promise.resolve({ office_users: [] });
}
async function fetchSources(query, dataset) {
  const response = await fetch("https://j1chatbottest.usgovvirginia.cloudapp.usgovcloudapi.net/api/sources", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": sessionToken
    },
    body: JSON.stringify({ message: query, dataset })
  });
  if (response.ok) {
    const sourcesData = await response.json();
    setSourceContent(sourcesData.content);
  } else {
    console.error("Error fetching sources:", await response.text());
  }
}

// Function to get user preferences
export const getUserPreferences = async (sessionToken) => {
  // Debug log the request
  const endpoint = "https://j1chatbottest.usgovvirginia.cloudapp.usgovcloudapi.net/api/user/preferences";
  console.log(`[DEBUG] Fetching user preferences from ${endpoint}`);
  
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: getAuthHeaders(sessionToken)
    });
    
    // Debug log the response status
    console.log(`[DEBUG] User preferences response status: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.text();
      console.log(`[DEBUG] Error response text: ${errorData}`);
      
      // If it's a 404, this could be a first-time user without preferences yet
      if (response.status === 404) {
        console.log("[DEBUG] No preferences found, returning defaults");
        // Return default values matching the backend defaults
        return {
          model: "mistral:latest", 
          temperature: 1.0,
          dataset: "KG",
          persona: "None"
        };
      }
      throw new Error(`Error fetching user preferences: ${errorData}`);
    }
    
    const data = await response.json();
    console.log(`[DEBUG] Received preferences: ${JSON.stringify(data)}`);
    
    // Map backend field names to frontend names for consistency
    return {
      model: data.selected_model,
      temperature: data.temperature,
      dataset: data.dataset,
      persona: data.persona
    };
  } catch (error) {
    console.error("Error in getUserPreferences:", error);
    
    // For any error, return default values to ensure the app works
    console.log("[DEBUG] Returning default preferences due to error");
    return {
      model: "mistral:latest", 
      temperature: 1.0,
      dataset: "KG",
      persona: "None"
    };
  }
};

// Function to update user preferences
export const updateUserPreferences = async (preferences, sessionToken) => {
  // Debug log the request
  const endpoint = "https://j1chatbottest.usgovvirginia.cloudapp.usgovcloudapi.net/api/user/preferences";
  console.log(`[DEBUG] Updating user preferences at ${endpoint}`);
  console.log(`[DEBUG] Preferences being sent: ${JSON.stringify(preferences)}`);
  
  try {
    // Convert from frontend field names to backend field names
    const backendPreferences = {
      selected_model: preferences.model,
      temperature: preferences.temperature,
      dataset: preferences.dataset,
      persona: preferences.persona
    };

    console.log(`[DEBUG] Converted preferences: ${JSON.stringify(backendPreferences)}`);

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: getAuthHeaders(sessionToken),
      body: JSON.stringify(backendPreferences)
    });
    
    // Debug log the response status
    console.log(`[DEBUG] Update preferences response status: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.text();
      console.log(`[DEBUG] Error response text: ${errorData}`);
      
      // If it's a 404, try to handle gracefully
      if (response.status === 404) {
        console.log("[DEBUG] Preferences endpoint not found, returning input values");
        // Return the input values as if they were saved
        return preferences;
      }
      
      throw new Error(`Error updating user preferences: ${errorData}`);
    }
    
    const data = await response.json();
    console.log(`[DEBUG] Received updated preferences: ${JSON.stringify(data)}`);
    
    // Map backend field names back to frontend names
    return {
      model: data.selected_model,
      temperature: data.temperature,
      dataset: data.dataset,
      persona: data.persona
    };
  } catch (error) {
    console.error("Error in updateUserPreferences:", error);
    
    // For any error, return the input preferences to avoid UI disruption
    console.log("[DEBUG] Returning input preferences due to error");
    return preferences;
  }
};

// Function to get available personas
export const getPersonas = async () => {
    try {
        const response = await fetch(`${BASE_URL}/api/personas`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                // No Authorization needed for this public endpoint
            },
        });
        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`Error fetching personas: ${errorData}`);
        }
        return await response.json(); // Returns the list of persona names
    } catch (error) {
        console.error("Error in getPersonas:", error);
        throw error; // Re-throw the error to be handled by the caller
    }
};

// Fetch chat histories for the current user
export const getChatHistories = async (sessionToken) => {
    try {
        const response = await fetch(`${BASE_URL}/api/chat_histories`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': sessionToken
            },
        });
        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`Error fetching chat histories: ${errorData}`);
        }
        return await response.json(); // Returns the list of chat histories
    } catch (error) {
        console.error("Error in getChatHistories:", error);
        throw error; // Re-throw the error to be handled by the caller
    }
};


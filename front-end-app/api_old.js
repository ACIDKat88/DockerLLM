import axios from 'axios';
import { useEffect } from 'react';

export const BASE_URL = "https://j1chatbottest.usgovvirginia.cloudapp.usgovcloudapi.net";

/**
 * handleResponse
 * Logs the response status and parses the JSON payload if the response is OK,
 * otherwise throws an error with the server’s error message (if available).
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
export async function fetchOffices() {
  console.log("[DEBUG] Fetching offices from /api/offices");
  return fetch(`${BASE_URL}/offices`)
    .then(handleResponse)
    .catch(handleError);
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
  
  return fetch(`${BASE_URL}/logout`, {
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

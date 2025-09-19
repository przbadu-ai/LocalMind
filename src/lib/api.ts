/**
 * API configuration and utilities for the Local Mind application.
 */

// Use unique port to avoid conflicts with other services
export const API_BASE_URL = 'http://localhost:52817';
export const API_PREFIX = '/api/v1';

/**
 * Constructs full API endpoint URL
 * @param endpoint - The endpoint path (e.g., '/config', '/health')
 * @returns Full URL for the API endpoint
 */
export function apiUrl(endpoint: string): string {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}${API_PREFIX}${cleanEndpoint}`;
}

/**
 * Default fetch options with proper headers
 */
export const defaultFetchOptions: RequestInit = {
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Helper function to make API requests
 * @param endpoint - The endpoint path
 * @param options - Fetch options
 * @returns Promise with the response
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(apiUrl(endpoint), {
    ...defaultFetchOptions,
    ...options,
    headers: {
      ...defaultFetchOptions.headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return response.json();
}
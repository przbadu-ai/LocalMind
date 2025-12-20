/**
 * Application version information
 *
 * Version is injected at build time via environment variables.
 * Falls back to package.json version in development.
 */

// These are replaced at build time by Vite
export const VERSION = import.meta.env.VITE_APP_VERSION || "0.0.0-dev";
export const GIT_COMMIT = import.meta.env.VITE_GIT_COMMIT || "dev";
export const BUILD_TIME = import.meta.env.VITE_BUILD_TIME || new Date().toISOString();

export interface VersionInfo {
  version: string;
  commit: string;
  service: string;
}

/**
 * Fetch backend version information
 */
export async function getBackendVersion(): Promise<VersionInfo | null> {
  try {
    // Use relative path - nginx will proxy to backend
    const response = await fetch("/version");
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error("Failed to fetch backend version:", error);
  }
  return null;
}

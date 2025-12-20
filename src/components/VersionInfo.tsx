/**
 * Version Information Component
 *
 * Displays frontend and backend version information.
 */

import { useEffect, useState } from "react";
import { VERSION, GIT_COMMIT, getBackendVersion, type VersionInfo } from "@/config/version";

export function VersionInfoDisplay() {
  const [backendVersion, setBackendVersion] = useState<VersionInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getBackendVersion()
      .then(setBackendVersion)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="text-xs text-muted-foreground space-y-1">
      <div className="flex items-center gap-2">
        <span className="font-medium">Frontend:</span>
        <span>v{VERSION}</span>
        {GIT_COMMIT !== "dev" && (
          <span className="text-muted-foreground/60">({GIT_COMMIT})</span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="font-medium">Backend:</span>
        {loading ? (
          <span className="text-muted-foreground/60">Loading...</span>
        ) : backendVersion ? (
          <>
            <span>v{backendVersion.version}</span>
            {backendVersion.commit !== "unknown" && (
              <span className="text-muted-foreground/60">({backendVersion.commit})</span>
            )}
          </>
        ) : (
          <span className="text-destructive">Unavailable</span>
        )}
      </div>
    </div>
  );
}

/**
 * Compact version display for footer/sidebar
 */
export function VersionBadge() {
  return (
    <span className="text-[10px] text-muted-foreground/50">
      v{VERSION}
    </span>
  );
}

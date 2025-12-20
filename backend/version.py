"""Version information for LocalMind backend."""

import os
from pathlib import Path

# Try to read version from VERSION file (created at build time)
# Falls back to a default if not found
_VERSION_FILE = Path(__file__).parent.parent / "VERSION"
_BACKEND_VERSION_FILE = Path(__file__).parent / "VERSION"


def get_version() -> str:
    """Get the application version."""
    # Check for VERSION file in backend directory first (Docker builds)
    if _BACKEND_VERSION_FILE.exists():
        return _BACKEND_VERSION_FILE.read_text().strip()

    # Check for VERSION file in project root (development)
    if _VERSION_FILE.exists():
        return _VERSION_FILE.read_text().strip()

    # Check environment variable (set during Docker build)
    if os.environ.get("APP_VERSION"):
        return os.environ["APP_VERSION"]

    return "0.0.0-dev"


def get_git_commit() -> str:
    """Get the git commit hash if available."""
    # Check environment variable (set during Docker build)
    if os.environ.get("GIT_COMMIT"):
        return os.environ["GIT_COMMIT"][:8]

    # Try to read from .git (development)
    git_head = Path(__file__).parent.parent / ".git" / "HEAD"
    if git_head.exists():
        ref = git_head.read_text().strip()
        if ref.startswith("ref: "):
            ref_path = Path(__file__).parent.parent / ".git" / ref[5:]
            if ref_path.exists():
                return ref_path.read_text().strip()[:8]
        return ref[:8]

    return "unknown"


VERSION = get_version()
GIT_COMMIT = get_git_commit()

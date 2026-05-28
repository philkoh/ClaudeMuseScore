"""
Cross-platform locator for the MuseScore binary built in this repo.

Resolution order:
  1. $MSCORE_PATH environment variable (if set and exists)
  2. Platform-specific built-in-this-repo location
  3. System-installed MuseScore (PATH lookup)
"""

import os
import platform
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


def find_mscore():
    """Return the path to the MuseScore binary, or None if not found."""
    env = os.environ.get('MSCORE_PATH')
    if env and Path(env).exists():
        return env

    for candidate in _local_build_candidates():
        if candidate.exists():
            return str(candidate)

    for name in _system_candidates():
        found = shutil.which(name)
        if found:
            return found

    return None


def _local_build_candidates():
    """Possible binary locations inside this repo's build tree."""
    build_dir = REPO_ROOT / "MuseScore" / "build" / "install"
    if platform.system() == "Windows":
        return [
            build_dir / "bin" / "MuseScore5.exe",
            build_dir / "bin" / "mscore.exe",
            REPO_ROOT / "MuseScore" / "build" / "Release" / "MuseScore5.exe",
        ]
    elif platform.system() == "Darwin":
        return [
            build_dir / "mscore.app" / "Contents" / "MacOS" / "mscore",
            build_dir / "bin" / "mscore",
        ]
    else:
        return [build_dir / "bin" / "mscore"]


def _system_candidates():
    """Names to try via PATH if the in-repo build isn't found."""
    if platform.system() == "Windows":
        return ["MuseScore5.exe", "MuseScore4.exe", "mscore.exe"]
    return ["mscore", "musescore", "MuseScore5", "MuseScore4"]


def require_mscore():
    """Return the path to MuseScore, or raise FileNotFoundError."""
    p = find_mscore()
    if not p:
        raise FileNotFoundError(
            "Could not locate MuseScore binary. Set $MSCORE_PATH or build it in MuseScore/build/."
        )
    return p

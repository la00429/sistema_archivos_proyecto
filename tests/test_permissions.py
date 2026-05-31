import os
import sys
import tempfile
import pytest
from pyfsmanager.permissions import (
    FilePermissions, parse_permissions, parse_chmod_symbolic,
    get_file_permissions, set_file_permissions,
    _get_current_username, _parse_icacls_flags,
)

def test_permissions_normalization():
    p = FilePermissions("r-x", "w-x", "rw-")
    assert p.user == "r-x"
    # w-x gets normalized: r is absent, w is present, x is present -> "-wx"
    assert p.group == "-wx"
    assert p.other == "rw-"

def test_permissions_from_octal():
    p = FilePermissions.from_octal(0o755)
    assert p.user == "rwx"
    assert p.group == "r-x"
    assert p.other == "r-x"

    p = FilePermissions.from_octal(0o600)
    assert p.user == "rw-"
    assert p.group == "---"
    assert p.other == "---"

def test_permissions_from_symbolic():
    p = FilePermissions.from_symbolic("rwxr-xr-x")
    assert p.user == "rwx"
    assert p.group == "r-x"
    assert p.other == "r-x"

def test_permissions_to_octal():
    p = FilePermissions("rwx", "r-x", "r-x")
    assert p.to_octal() == 0o755

def test_permissions_to_symbolic():
    p = FilePermissions("rwx", "r-x", "r-x")
    assert p.to_symbolic() == "rwxr-xr-x"

def test_parse_permissions():
    p = FilePermissions("rwx", "r-x", "r-x")
    assert parse_permissions(p) == p
    assert parse_permissions(0o755) == p
    assert parse_permissions("rwxr-xr-x") == p
    assert parse_permissions("755") == p

def test_parse_chmod_symbolic():
    # Base: 0o755 (rwxr-xr-x)
    # Add write to group: g+w -> 0o775 (rwxrwxr-x)
    assert parse_chmod_symbolic(0o755, "g+w") == 0o775
    # Remove execute from all: a-x -> 0o644 (rw-r--r--)
    assert parse_chmod_symbolic(0o755, "a-x") == 0o644
    # Set user to rw, group/other to r: u=rw,go=r -> 0o644 (rw-r--r--)
    assert parse_chmod_symbolic(0o755, "u=rw,go=r") == 0o644

def test_get_and_set_file_permissions():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    try:
        # Set to rw-r--r--
        set_file_permissions(path, 0o644)
        perms = get_file_permissions(path)
        
        if sys.platform != 'win32':
            # Strict POSIX test
            assert perms.to_octal() == 0o644
            assert perms.to_symbolic() == "rw-r--r--"
        else:
            # On Windows, we map ACLs. Let's make sure it's readable and writable
            assert 'r' in perms.user
            assert 'w' in perms.user
    finally:
        os.unlink(path)

# --- Regression tests for fixed bugs ---

def test_get_current_username_never_raises():
    """Bug 3 regression: _get_current_username() must never raise, even without TTY."""
    name = _get_current_username()
    assert isinstance(name, str)
    assert len(name) > 0

def test_parse_icacls_flags_full():
    """Bug 2 regression: (F) flag must map to rwx."""
    assert _parse_icacls_flags("DOMAIN\\user:(F)") == "rwx"

def test_parse_icacls_flags_modify():
    """Bug 2 regression: (M) flag must map to rwx (Modify includes read, write, execute)."""
    assert _parse_icacls_flags("user:(M)") == "rwx"

def test_parse_icacls_flags_rx():
    """Bug 2 regression: (RX) flag must map to r-x."""
    assert _parse_icacls_flags("user:(RX)") == "r-x"

def test_parse_icacls_flags_read_only():
    """Bug 2 regression: (R) flag must map to r--."""
    assert _parse_icacls_flags("user:(R)") == "r--"

def test_parse_icacls_flags_with_inheritance():
    """Bug 2 regression: inheritance markers (I)(OI)(CI) must be ignored."""
    assert _parse_icacls_flags("BUILTIN\\Users:(I)(RX)") == "r-x"
    assert _parse_icacls_flags("Everyone:(OI)(CI)(F)") == "rwx"

@pytest.mark.skipif(sys.platform != 'win32', reason="Windows-only test")
def test_get_windows_permissions_icacls_returns_valid():
    """Bug 2 regression: icacls fallback must return a valid FilePermissions object."""
    from pyfsmanager.permissions import get_windows_permissions_icacls
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    try:
        perms = get_windows_permissions_icacls(path)
        assert isinstance(perms, FilePermissions)
        for rwx in (perms.user, perms.group, perms.other):
            assert len(rwx) == 3
            assert all(c in 'rwx-' for c in rwx)
    finally:
        os.unlink(path)

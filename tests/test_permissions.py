import os
import sys
import tempfile
import pytest
from pyfsmanager.permissions import FilePermissions, parse_permissions, parse_chmod_symbolic, get_file_permissions, set_file_permissions

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

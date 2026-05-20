import os
import sys
import tempfile
import time
import pytest
from pyfsmanager.metadata import get_metadata, set_file_times

def test_get_metadata():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Hello World")
        path = f.name
    try:
        meta = get_metadata(path)
        assert meta.name == os.path.basename(path)
        assert meta.size == 11
        assert meta.type == 'regular'
        assert meta.atime is not None
        assert meta.mtime is not None
        assert meta.ctime is not None
        if sys.platform == 'win32':
            assert meta.birthtime is not None
    finally:
        os.unlink(path)

def test_set_times():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    try:
        # Define historical times
        t_access = time.time() - 3600
        t_modify = time.time() - 7200
        t_create = time.time() - 10800

        set_file_times(path, atime=t_access, mtime=t_modify, birthtime=t_create)
        
        meta = get_metadata(path)
        
        # Verify access and modification times (with small tolerance)
        assert abs(meta.atime - t_access) < 2
        assert abs(meta.mtime - t_modify) < 2
        
        if sys.platform == 'win32':
            # Verify birthtime on Windows
            assert abs(meta.birthtime - t_create) < 2
    finally:
        os.unlink(path)

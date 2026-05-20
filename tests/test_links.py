import os
import sys
import tempfile
import pytest
from pyfsmanager.links import (
    create_hard_link, 
    create_symbolic_link, 
    create_junction, 
    read_link, 
    is_junction, 
    is_symlink
)

def test_hard_links():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        src = f.name
        f.write(b"data")
    dst = src + ".hard"
    try:
        create_hard_link(src, dst)
        assert os.path.exists(dst)
        assert not os.path.islink(dst)
        # Verify content
        with open(dst, 'rb') as f:
            assert f.read() == b"data"
    finally:
        os.unlink(src)
        if os.path.exists(dst):
            os.unlink(dst)

def test_symbolic_links():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        src = f.name
        f.write(b"data")
    dst = src + ".sym"
    try:
        try:
            create_symbolic_link(src, dst)
            assert os.path.islink(dst)
            assert is_symlink(dst)
            assert read_link(dst) == src
        except OSError as e:
            # On Windows, creating symlinks requires admin privileges or developer mode.
            # If it fails due to privilege, skip this assertion gracefully.
            if sys.platform == 'win32' and (e.winerror == 1314 or "[WinError 1314]" in str(e)):
                pytest.skip("Skipping symlink test: missing privilege on Windows (enable Developer Mode)")
            else:
                raise e
    finally:
        os.unlink(src)
        if os.path.exists(dst):
            os.unlink(dst)

@pytest.mark.skipif(sys.platform != 'win32', reason="Junctions are only supported on Windows")
def test_junctions():
    # Junctions require a directory target
    tmp_dir = tempfile.mkdtemp()
    src = os.path.join(tmp_dir, "target_dir")
    os.mkdir(src)
    
    # Write a file in the target directory
    test_file = os.path.join(src, "file.txt")
    with open(test_file, 'w') as f:
        f.write("inside junction")
        
    dst = os.path.join(tmp_dir, "junction_link")
    
    try:
        create_junction(src, dst)
        assert os.path.isdir(dst)
        assert is_junction(dst)
        assert not is_symlink(dst)
        assert os.path.abspath(read_link(dst)) == os.path.abspath(src)
        
        # Verify nested access
        link_file = os.path.join(dst, "file.txt")
        assert os.path.exists(link_file)
        with open(link_file, 'r') as f:
            assert f.read() == "inside junction"
            
        # Delete junction (must not delete the target directory contents)
        os.rmdir(dst)
        assert not os.path.exists(dst)
        assert os.path.exists(test_file)
    finally:
        if os.path.exists(dst):
            os.rmdir(dst)
        if os.path.exists(test_file):
            os.unlink(test_file)
        if os.path.exists(src):
            os.rmdir(src)
        os.rmdir(tmp_dir)

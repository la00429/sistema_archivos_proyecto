import os
import sys
import tempfile
import pytest
from pyfsmanager.manager import FSManager

def test_read_write_text():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    try:
        # Write text with accented characters
        content = "Hola, esto es una prueba con acentos: áéíóú ñ!"
        FSManager.write_file(path, content, encoding='utf-8')
        
        # Read file (should auto-detect encoding)
        read_content = FSManager.read_file(path)
        assert read_content == content
    finally:
        os.unlink(path)

def test_read_write_binary():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    try:
        # Write binary content (null byte inside)
        content = b"\x00\x01\x02\x03\x04\x05Hola\x00Mundo\xff"
        FSManager.write_file(path, content)
        
        # Read file (should auto-detect binary mode)
        read_content = FSManager.read_file(path)
        assert read_content == content
    finally:
        os.unlink(path)

def test_touch_mkdir_delete():
    tmp_dir = tempfile.mkdtemp()
    test_dir = os.path.join(tmp_dir, "nested", "dir")
    test_file = os.path.join(test_dir, "test.txt")
    
    try:
        # Test mkdir (recursive)
        FSManager.mkdir(test_dir)
        assert os.path.isdir(test_dir)
        
        # Test touch
        FSManager.touch(test_file)
        assert os.path.exists(test_file)
        assert os.path.getsize(test_file) == 0
        
        # Test write and read
        FSManager.write_file(test_file, "content")
        assert FSManager.read_file(test_file) == "content"
        
        # Test delete (file)
        FSManager.delete(test_file)
        assert not os.path.exists(test_file)
        
        # Test delete (directory)
        FSManager.delete(test_dir)
        assert not os.path.exists(test_dir)
    finally:
        if os.path.exists(tmp_dir):
            shutil_path = tmp_dir
            import shutil
            shutil.rmtree(shutil_path)

def test_copy_move():
    tmp_dir = tempfile.mkdtemp()
    src = os.path.join(tmp_dir, "src.txt")
    dst_copy = os.path.join(tmp_dir, "copy.txt")
    dst_move = os.path.join(tmp_dir, "move.txt")
    
    try:
        FSManager.write_file(src, "data")
        
        # Test Copy
        FSManager.copy(src, dst_copy)
        assert os.path.exists(dst_copy)
        assert FSManager.read_file(dst_copy) == "data"
        
        # Test Move
        FSManager.move(dst_copy, dst_move)
        assert not os.path.exists(dst_copy)
        assert os.path.exists(dst_move)
        assert FSManager.read_file(dst_move) == "data"
    finally:
        import shutil
        shutil.rmtree(tmp_dir)

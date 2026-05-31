import os
import sys
import tempfile
import pytest
from pyfsmanager.manager import FSManager
from pyfsmanager.metadata import get_metadata

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
            import shutil
            shutil.rmtree(tmp_dir)

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

# --- Regression tests for fixed bugs ---

def test_utf8_bom_no_duplication():
    """Bug 9 regression: overwriting a UTF-8 BOM file must not duplicate the BOM."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        path = f.name
    try:
        # Write a file with UTF-8 BOM manually
        with open(path, 'wb') as f:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            f.write('Hola mundo'.encode('utf-8'))

        # Overwrite using FSManager (detects utf-8-sig and must NOT duplicate BOM)
        FSManager.write_file(path, "Hola mundo editado")

        with open(path, 'rb') as f:
            raw = f.read()

        bom = b'\xef\xbb\xbf'
        # The BOM must appear AT MOST once at the start
        assert raw.count(bom) <= 1, f"BOM was duplicated! Raw bytes start: {raw[:12]!r}"
    finally:
        os.unlink(path)


def test_metadata_nlink():
    """Mejora 1: FileMetadata must expose nlink (hard link count)."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    try:
        meta = get_metadata(path)
        assert hasattr(meta, 'nlink'), "FileMetadata must have nlink attribute"
        assert isinstance(meta.nlink, int)
        assert meta.nlink >= 1
        # nlink must also appear in to_dict()
        d = meta.to_dict()
        assert 'nlink' in d
        assert d['nlink'] == meta.nlink
    finally:
        os.unlink(path)


def test_delete_nonexistent_raises():
    """Edge case: deleting a non-existent path must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        FSManager.delete("/this/path/does/not/exist/at/all_xyz_999")


def test_copy_directory():
    """Edge case: copying a directory must copy its contents recursively."""
    tmp = tempfile.mkdtemp()
    try:
        src_dir = os.path.join(tmp, "src_dir")
        os.makedirs(src_dir)
        src_file = os.path.join(src_dir, "file.txt")
        FSManager.write_file(src_file, "contenido de prueba")

        dst_dir = os.path.join(tmp, "dst_dir")
        FSManager.copy(src_dir, dst_dir)

        assert os.path.isdir(dst_dir)
        copied_file = os.path.join(dst_dir, "file.txt")
        assert os.path.exists(copied_file)
        assert FSManager.read_file(copied_file) == "contenido de prueba"
    finally:
        import shutil
        shutil.rmtree(tmp)

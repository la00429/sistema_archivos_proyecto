import os
import shutil
import sys
from typing import Union, Optional

from .utils import detect_file_type, detect_encoding
from .permissions import FilePermissions, set_file_permissions, get_file_permissions
from .metadata import FileMetadata, get_metadata, set_file_times
from .links import (
    create_hard_link, 
    create_symbolic_link, 
    create_junction, 
    read_link, 
    is_junction, 
    is_symlink
)

class FSManager:
    @staticmethod
    def get_metadata(path: str) -> FileMetadata:
        """
        Retrieves complete metadata for the given path.
        """
        return get_metadata(path)

    @staticmethod
    def set_permissions(path: str, permissions: Union[FilePermissions, int, str]) -> None:
        """
        Sets permissions on a file or directory.
        Accepts FilePermissions, octal int (e.g. 0o755), octal string ('755'),
        symbolic permission string ('rwxr-xr-x'), or chmod expression ('u+w,go-rx').
        """
        set_file_permissions(path, permissions)

    @staticmethod
    def set_times(
        path: str, 
        atime: Optional[float] = None, 
        mtime: Optional[float] = None, 
        birthtime: Optional[float] = None
    ) -> None:
        """
        Sets access (atime), modification (mtime), and creation (birthtime) timestamps.
        """
        set_file_times(path, atime, mtime, birthtime)

    @staticmethod
    def create_link(link_type: str, src: str, dst: str) -> None:
        """
        Creates a link. link_type can be 'hard', 'symlink' (or 'sym'), or 'junction'.
        """
        link_type = link_type.lower()
        if link_type == 'hard':
            create_hard_link(src, dst)
        elif link_type in ('symlink', 'sym'):
            create_symbolic_link(src, dst)
        elif link_type == 'junction':
            create_junction(src, dst)
        else:
            raise ValueError(f"Unknown link type: {link_type}. Supported: hard, symlink, junction.")

    @classmethod
    def read_file(cls, path: str) -> Union[str, bytes]:
        """
        Reads file content. Detects text vs binary automatically.
        If it's text, it decodes and returns a string. If it's binary, it returns bytes.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
            
        ftype = detect_file_type(path)
        if ftype == 'binary':
            with open(path, 'rb') as f:
                return f.read()
        else:
            encoding = detect_encoding(path)
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                return f.read()

    @staticmethod
    def write_file(path: str, content: Union[str, bytes], encoding: Optional[str] = None) -> None:
        """
        Writes content to a file.
        If content is a string, writes in text mode (using detected or specified encoding).
        If content is bytes, writes in binary mode.

        Note: when the detected encoding is 'utf-8-sig' (UTF-8 with BOM) and the
        file already exists, we write with plain 'utf-8' to avoid re-inserting the
        BOM and duplicating it. The BOM is only needed on the first byte of a new file.
        """
        if isinstance(content, bytes):
            with open(path, 'wb') as f:
                f.write(content)
        else:
            if encoding is None:
                if os.path.exists(path):
                    encoding = detect_encoding(path)
                else:
                    encoding = 'utf-8'
            # Bug 9 fix: utf-8-sig re-inserts the BOM on every write, duplicating it
            # when overwriting an existing BOM file. Use plain utf-8 for overwrite.
            write_encoding = 'utf-8' if (encoding == 'utf-8-sig' and os.path.exists(path)) else encoding
            with open(path, 'w', encoding=write_encoding, errors='replace') as f:
                f.write(content)

    @staticmethod
    def touch(path: str) -> None:
        """
        Creates an empty file if it doesn't exist, or updates its atime and mtime to current.
        """
        if os.path.exists(path):
            os.utime(path, None)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                pass

    @staticmethod
    def mkdir(path: str, recursive: bool = True) -> None:
        """
        Creates a directory. By default creates parent directories recursively.
        """
        if recursive:
            os.makedirs(path, exist_ok=True)
        else:
            os.mkdir(path)

    @classmethod
    def delete(cls, path: str) -> None:
        """
        Deletes a file, directory, symlink, or junction.
        Handles nested items and prevents recursion into symlinks/junctions.
        """
        if not os.path.exists(path) and not os.path.islink(path):
            raise FileNotFoundError(f"Path not found: {path}")

        if is_junction(path) or os.path.islink(path):
            if sys.platform == 'win32' and os.path.isdir(path):
                os.rmdir(path)  # removes junctions and directory symlinks
            else:
                os.unlink(path)  # removes file symlinks/links
        elif os.path.isdir(path):
            # To be extra safe with nested junctions inside a directory,
            # we traverse and delete links first, then delete the rest.
            cls._delete_tree_custom(path)
        else:
            os.unlink(path)

    @classmethod
    def _delete_tree_custom(cls, path: str) -> None:
        """
        Helper that recursively deletes directory contents,
        ensuring junctions/symlinks are unlinked rather than traversed.
        """
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if is_junction(item_path) or os.path.islink(item_path):
                if sys.platform == 'win32' and os.path.isdir(item_path):
                    os.rmdir(item_path)
                else:
                    os.unlink(item_path)
            elif os.path.isdir(item_path):
                cls._delete_tree_custom(item_path)
            else:
                os.unlink(item_path)
        os.rmdir(path)

    @classmethod
    def copy(cls, src: str, dst: str) -> None:
        """
        Copies a file, directory, symlink, or junction.
        Recreates junctions and symlinks instead of copying their targets.
        """
        if not os.path.exists(src) and not os.path.islink(src):
            raise FileNotFoundError(f"Source path not found: {src}")

        if is_junction(src):
            target = read_link(src)
            create_junction(target, dst)
        elif is_symlink(src):
            target = read_link(src)
            create_symbolic_link(target, dst, is_dir=os.path.isdir(src))
        elif os.path.isdir(src):
            cls._copy_tree_custom(src, dst)
        else:
            shutil.copy2(src, dst)

    @classmethod
    def _copy_tree_custom(cls, src_dir: str, dst_dir: str) -> None:
        """
        Helper that recursively copies a directory, recreating junctions and symlinks.
        """
        os.makedirs(dst_dir, exist_ok=True)
        for item in os.listdir(src_dir):
            s_item = os.path.join(src_dir, item)
            d_item = os.path.join(dst_dir, item)
            if is_junction(s_item):
                target = read_link(s_item)
                create_junction(target, d_item)
            elif is_symlink(s_item):
                target = read_link(s_item)
                create_symbolic_link(target, d_item, is_dir=os.path.isdir(s_item))
            elif os.path.isdir(s_item):
                cls._copy_tree_custom(s_item, d_item)
            else:
                shutil.copy2(s_item, d_item)

    @staticmethod
    def move(src: str, dst: str) -> None:
        """
        Moves (renames) a file or directory.
        """
        if not os.path.exists(src) and not os.path.islink(src):
            raise FileNotFoundError(f"Source path not found: {src}")
        shutil.move(src, dst)
